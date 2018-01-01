"use strict";
const express = require('express');

const bodyParser = require('body-parser');
const transfer = require("./lib/iota.flash.js/lib/transfer");
const multisig = require("./lib/iota.flash.js/lib/multisig");
const helper = require("./lib/helper");
const storage = require("./lib/storage");

let app = express();

const SEED = process.env.IOTA_SEED;

// Default configurations
const SECURITY = 2;
const SIGNERS_COUNT = 2; // Number of parties taking signing part in the channel
const TREE_DEPTH = 4; // Flash tree depth
const CHANNEL_BALANCE = 2000; // Total channel Balance
const DEPOSITS = [1000, 1000]; // Users deposits

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: false}));

app.post('/init', function (req, res) {

    // ToDo: validate input

    let initValues = req.body;
    console.log(`Initialing flash with ${JSON.stringify(initValues)}`);

    // initialise flash object
    let flash = {
        userIndex: 0,
        index: 0,
        security: initValues.security || SECURITY,
        depth: initValues.depth || TREE_DEPTH,
        bundles: [],
        partialDigests: [],
        flash: {
            signersCount: initValues.signersCount || SIGNERS_COUNT,
            balance: initValues.balance || CHANNEL_BALANCE,
            deposit: initValues.deposit || DEPOSITS.slice(),
            outputs: {},
            transfers: []
        }
    };

    // create digests for the start of the channel
    for (let i = 0; i < flash.depth + 1; i++) {
        // Create new digest
        const digest = multisig.getDigest(
            SEED,
            flash.index,
            flash.security
        );
        // Increment key index
        flash.index++;
        flash.partialDigests.push(digest);
    }

    storage.set('flash', flash);
    console.log(`Initialised flash ${JSON.stringify(flash)}`);

    res.json(flash);
});

app.get('/flash', function (req, res) {
    res.json(storage.get('flash'));
});

// app.route('/store')
//     .post(function (req, res) {
//         storage.set('dummy', req.body);
//         res.send('ok')
//     })
//     .get(function (req, res) {
//         res.json(storage.get('dummy'));
//     });


app.listen(3000, function () {
    console.log('Flash server listening on port 3000!');
});