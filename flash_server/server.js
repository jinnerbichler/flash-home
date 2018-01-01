"use strict";
const express = require('express');

const bodyParser = require('body-parser');
const IOTACrypto = require("iota.crypto.js");
const transfers = require("iota.flash.js").transfer;
const multisig = require("iota.flash.js").multisig;
const flashHelper = require("./helper");

let app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: false}));

app.get('/', function(req, res) {
    res.send('hell0');
});

app.listen(3000, function () {
    console.log('Flash server listening on port 3000!');
});