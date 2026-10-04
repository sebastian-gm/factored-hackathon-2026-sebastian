import { test, expect } from "@playwright/test";
import { mkdtempSync, readFileSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import path from "node:path";
import { reserveLiveTurn } from "./helpers/judge-tour";

const keys = ["JUDGE_TOUR_PAID", "JUDGE_TOUR_MAX_TURNS", "JUDGE_TOUR_TURN_LEDGER"] as const;
let original: (string | undefined)[];
let folder: string;
test.beforeEach(() => {
  original = keys.map((key) => process.env[key]);
  const root = path.resolve("../../artifacts/ux-audit/go-live/guard-tests");
  mkdirSync(root, { recursive: true, mode: 0o700 });
  folder = mkdtempSync(path.join(root, "run-"));
  process.env.JUDGE_TOUR_TURN_LEDGER = path.join(folder, "turns.json");
  process.env.JUDGE_TOUR_PAID = "1";
  process.env.JUDGE_TOUR_MAX_TURNS = "2";
});
test.afterEach(() => {
  keys.forEach((key, i) => {
    if (original[i] === undefined) delete process.env[key];
    else process.env[key] = original[i];
  });
  rmSync(folder, { recursive: true, force: true });
});
test("live turn guard requires opt-in and a finite bounded cap", () => {
  process.env.JUDGE_TOUR_PAID = "0";
  expect(() => reserveLiveTurn()).toThrow();
  process.env.JUDGE_TOUR_PAID = "1";
  for (const value of ["0", "41", "NaN", "Infinity", "1.5"]) {
    process.env.JUDGE_TOUR_MAX_TURNS = value;
    expect(() => reserveLiveTurn()).toThrow();
  }
});
test("live turn guard persists attempted sends and cannot raise a previous cap", () => {
  reserveLiveTurn();
  process.env.JUDGE_TOUR_MAX_TURNS = "40";
  reserveLiveTurn();
  expect(() => reserveLiveTurn()).toThrow();
  expect(JSON.parse(readFileSync(process.env.JUDGE_TOUR_TURN_LEDGER!, "utf8"))).toEqual({ attempts: 2, maximum: 2 });
});
test("live turn guard fails closed on crashed locks and invalid accounting", () => {
  mkdirSync(process.env.JUDGE_TOUR_TURN_LEDGER! + ".lock");
  expect(() => reserveLiveTurn()).toThrow();
  rmSync(process.env.JUDGE_TOUR_TURN_LEDGER! + ".lock", { recursive: true });
  writeFileSync(process.env.JUDGE_TOUR_TURN_LEDGER!, "{}");
  expect(() => reserveLiveTurn()).toThrow();
});
test("live turn guard refuses paths outside ignored artifacts", () => {
  process.env.JUDGE_TOUR_TURN_LEDGER = path.resolve("tour-ledger-forbidden.json");
  expect(() => reserveLiveTurn()).toThrow();
});
