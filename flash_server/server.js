"use strict";
const express = require('express');
const bodyParser = require('body-parser');
const transfer = require("./lib/iota.flash.js/lib/transfer");
const multisig = require("./lib/iota.flash.js/lib/multisig");
const flashUtils = require("./lib/flash-utils");
const storage = require("./lib/storage");

const SEED = process.env.IOTA_SEED;

// default configurations
const SECURITY = 2;
const SIGNERS_COUNT = 2; // number of parties taking signing part in the channel
const TREE_DEPTH = 4; // flash tree depth
const CHANNEL_BALANCE = 2000; // total channel Balance
const DEPOSITS = [1000, 1000]; // users deposits

let app = express();
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: false}));

// -------------------------------------------------
// -------------- Flash Intialisation --------------
// -------------------------------------------------
app.put('/init', function (req, res) {

    // ToDo: validate input

    let initValues = req.body;
    console.log(`Initialing flash with ${JSON.stringify(initValues)}`);

    // initialise flash object
    let flash = {
        userIndex: initValues.userIndex,
        index: initValues.index,
        security: initValues.security || SECURITY,
        depth: initValues.depth || TREE_DEPTH,
        bundles: [],
        partialDigests: [],
        flash: {
            signersCount: initValues.signersCount || SIGNERS_COUNT,
            balance: initValues.balance || CHANNEL_BALANCE,
            deposit: initValues.deposit || DEPOSITS,
            outputs: {},
            transfers: []
        }
    };

    // create digests for the start of the channel
    for (let i = 0; i < flash.depth + 1; i++) {

        // create new digest
        const digest = multisig.getDigest(SEED, flash.index, flash.security);

        // increment key index
        flash.index++;
        flash.partialDigests.push(digest);
    }

    storage.set('flash', flash);
    console.log(`Initialised flash ${JSON.stringify(flash)}`);

    res.json(flash);
});

// -------------------------------------------------
// ------- Multisignature Address Generation -------
// -------------------------------------------------
app.post('/multisignature', function (req, res) {

    let allDigests = req.body.allDigests;
    console.log(`Creating ${allDigests[0].length} multisignature addresses for ${allDigests.length} users`);

    let flash = storage.get('flash');
    let multisignatureAddresses = flash.partialDigests.map((digest, index) => {
        // create address
        let addy = multisig.composeAddress(
            allDigests.map(userDigests => userDigests[index])
        );

        // add key index in
        addy.index = digest.index;

        // add the signing index to the object IMPORTANT
        addy.signingIndex = flash.userIndex * digest.security;

        // get the sum of all digest security to get address security sum
        addy.securitySum = allDigests
            .map(userDigests => userDigests[index])
            .reduce((acc, v) => acc + v.security, 0);

        // add Security
        addy.security = digest.security;
        return addy
    });

    // set remainder address (Same on both users)
    flash.flash.remainderAddress = multisignatureAddresses.shift();

    // nest trees
    for (let i = 1; i < multisignatureAddresses.length; i++) {
        multisignatureAddresses[i - 1].children.push(multisignatureAddresses[i])
    }

    // set Flash root
    flash.flash.root = multisignatureAddresses.shift();

    // update flash object
    storage.set('flash', flash);

    res.json(multisignatureAddresses)
});

// -------------------------------------------------
// ----------- Set Settlement Addresses ------------
// -------------------------------------------------
app.post('/settlement', function (req, res) {

    console.log('Adding settlement addresses');

    let flash = storage.get('flash');
    flash.flash.settlementAddresses = req.body.settlementAddresses;
    storage.set('flash', flash);
    res.json(flash);
});

// -------------------------------------------------
// ----------------- Transfer  ---------------------
// -------------------------------------------------
app.post('/transfer', function (req, res) {

    // ToDO: check each address if it is not the one in the flash object

    let transfers = req.body.transfers;
    console.log(`Bundling ${transfers.length} transfers`);

    let flash = storage.get('flash');
    let bundles = flashUtils.createTransaction(flash, transfers, false);

    res.json(bundles);
});

// -------------------------------------------------
// ----------------- Sign Transactions -------------
// -------------------------------------------------
app.post('/sign_transactions', function (req, res) {

    let bundles = req.body.bundles;
    console.log(`Signing ${bundles.length} transactions`);

    let flash = storage.get('flash');

    // get signatures for the bundles
    flash.userSeed = SEED;  // should not be stored or returned in response
    let signatures = flashUtils.signTransaction(flash, bundles);

    // sign bundle with signatures
    let signedBundles = transfer.appliedSignatures(bundles, signatures);

    res.json(signedBundles);
});

// -------------------------------------------------
// --------------- Apply Signed Bundles ------------
// -------------------------------------------------
app.post('/apply_signature', function (req, res) {

    let signedBundles = req.body.signedBundles;
    console.log(`Applying signature to ${signedBundles.length} bundles`);

    // apply transfers to user
    let flash = storage.get('flash');
    flash = flashUtils.applyTransfers(flash, signedBundles);

    // save latest channel bundles
    flash.bundles = signedBundles;
    storage.set('flash', flash);

    res.json(flash);
});

// -------------------------------------------------
// ------------------ Close Channel ----------------
// -------------------------------------------------
app.post('/close', function (req, res) {

    console.log('Closing channel');

    let flash = storage.get('flash');
    let bundles = flashUtils.createTransaction(flash, flash.flash.settlementAddresses, true);

    res.json(bundles);
});

// -------------------------------------------------
// -------------- Current Flash Object -------------
// -------------------------------------------------
app.get('/flash', function (req, res) {
    res.json(storage.get('flash'));
});

app.listen(3000, function () {
    console.log('Flash server listening on port 3000!');
});