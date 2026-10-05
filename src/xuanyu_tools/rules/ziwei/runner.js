"use strict";

const fs = require("fs");
const path = require("path");

global.self = global;
const iztro = require(path.join(__dirname, "vendor", "iztro.min.js"));

const ENGINE_VERSION = "2.5.8";

function fail(message) {
  process.stderr.write(String(message));
  process.exit(1);
}

function cleanStar(star) {
  return {
    name: star.name || "",
    type: star.type || "",
    scope: star.scope || "",
    brightness: star.brightness || "",
    mutagen: star.mutagen || "",
  };
}

function cleanStars(groups) {
  if (!Array.isArray(groups)) return [];
  return groups.map((group) =>
    Array.isArray(group) ? group.map(cleanStar) : [],
  );
}

function cleanScope(scope) {
  if (!scope) return null;
  const result = {
    index: scope.index,
    name: scope.name || "",
    heavenlyStem: scope.heavenlyStem || "",
    earthlyBranch: scope.earthlyBranch || "",
    palaceNames: Array.isArray(scope.palaceNames) ? scope.palaceNames : [],
    mutagen: Array.isArray(scope.mutagen) ? scope.mutagen : [],
    stars: cleanStars(scope.stars),
  };
  if (Number.isInteger(scope.nominalAge)) {
    result.nominalAge = scope.nominalAge;
  }
  if (scope.yearlyDecStar) {
    result.yearlyDecStar = {
      suiqian12: scope.yearlyDecStar.suiqian12 || [],
      jiangqian12: scope.yearlyDecStar.jiangqian12 || [],
    };
  }
  return result;
}

function cleanPalace(palace) {
  return {
    index: palace.index,
    name: palace.name || "",
    isBodyPalace: Boolean(palace.isBodyPalace),
    isOriginalPalace: Boolean(palace.isOriginalPalace),
    heavenlyStem: palace.heavenlyStem || "",
    earthlyBranch: palace.earthlyBranch || "",
    majorStars: (palace.majorStars || []).map(cleanStar),
    minorStars: (palace.minorStars || []).map(cleanStar),
    adjectiveStars: (palace.adjectiveStars || []).map(cleanStar),
    changsheng12: palace.changsheng12 || "",
    boshi12: palace.boshi12 || "",
    jiangqian12: palace.jiangqian12 || "",
    suiqian12: palace.suiqian12 || "",
    decadal: {
      range: palace.decadal && Array.isArray(palace.decadal.range)
        ? palace.decadal.range
        : [],
      heavenlyStem: palace.decadal ? palace.decadal.heavenlyStem || "" : "",
      earthlyBranch: palace.decadal ? palace.decadal.earthlyBranch || "" : "",
    },
    ages: Array.isArray(palace.ages) ? palace.ages : [],
  };
}

function parseTargetDate(value) {
  const match = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(value || "");
  if (!match) fail("invalid targetDate");
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day, 12, 0, 0, 0);
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    fail("invalid targetDate");
  }
  return date;
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, "utf8"));
  } catch (_) {
    fail("invalid json input");
  }

  const astrolabe = iztro.astro.withOptions({
    type: "solar",
    dateStr: input.birthDate,
    timeIndex: input.birthTimeIndex,
    gender: input.gender,
    fixLeap: input.fixLeap,
    language: "zh-CN",
    astroType: input.astroType,
    config: input.config,
  });
  const horoscope = astrolabe.horoscope(
    parseTargetDate(input.targetDate),
    input.targetTimeIndex,
  );

  const output = {
    engine: {
      name: "iztro",
      version: ENGINE_VERSION,
      license: "MIT",
    },
    astrolabe: {
      gender: astrolabe.gender,
      solarDate: astrolabe.solarDate,
      lunarDate: astrolabe.lunarDate,
      chineseDate: astrolabe.chineseDate,
      time: astrolabe.time,
      timeRange: astrolabe.timeRange,
      sign: astrolabe.sign,
      zodiac: astrolabe.zodiac,
      earthlyBranchOfBodyPalace: astrolabe.earthlyBranchOfBodyPalace,
      earthlyBranchOfSoulPalace: astrolabe.earthlyBranchOfSoulPalace,
      soul: astrolabe.soul,
      body: astrolabe.body,
      fiveElementsClass: astrolabe.fiveElementsClass,
      palaces: astrolabe.palaces.map(cleanPalace),
    },
    horoscope: {
      lunarDate: horoscope.lunarDate,
      solarDate: horoscope.solarDate,
      decadal: cleanScope(horoscope.decadal),
      age: cleanScope(horoscope.age),
      yearly: cleanScope(horoscope.yearly),
      monthly: cleanScope(horoscope.monthly),
      daily: cleanScope(horoscope.daily),
      hourly: cleanScope(horoscope.hourly),
    },
  };
  process.stdout.write(JSON.stringify(output));
}

try {
  main();
} catch (error) {
  fail(error && error.message ? error.message : error);
}
