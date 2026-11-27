// This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
// Parses fixtures with the compiled card script and prints normalized units as JSON.
// usage: node parity.js <compiled cards.js> <fixtures.json>
"use strict";
const fs = require("fs");
const vm = require("vm");

const [cardsPath, fixturesPath] = process.argv.slice(2);
// The parsers don't touch the DOM; generate() only queries it and finds nothing.
const context = vm.createContext({document: {querySelectorAll: () => []}});
vm.runInContext(fs.readFileSync(cardsPath, "utf8"), context, {filename: cardsPath});

const run = vm.runInContext(`(function(fixtures) {
	function accentStr(acc) {
		if(acc.value === null) return "?";
		if(Array.isArray(acc.value)) return acc.value.map(([ds, mc]) => ds + "@" + mc).join("-");
		return String(acc.value);
	}
	function normalize(unit) {
		return {
			text: unit.segments.map(s => s.text).join(""),
			reading: unit.segments.map(s => s.get_reading()).join(""),
			accent_reading: unit.accent_reading(),
			accents: unit.accents.map(accentStr),
			is_yougen: unit.is_yougen,
			uncertain: unit.uncertain,
		};
	}
	return fixtures.map(([syntax, value]) => {
		try {
			return {units: (syntax === "migaku" ? parse_migaku : parse_jrp)(value).map(normalize)};
		} catch(e) {
			return {error: String(e && e.message)};
		}
	});
})`, context);

process.stdout.write(JSON.stringify(run(JSON.parse(fs.readFileSync(fixturesPath, "utf8")))));
