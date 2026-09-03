import { describe, expect, it } from "vitest";

import { FailureReportPayload, submitFailureReport } from "./failureReportSubmission";

const payload: FailureReportPayload = {
  category: "MISUNDERSTOOD_PROPOSITION",
  summary: "The response changed the stated proposition.",
  expected_behavior: null,
  evaluation_case_id: null,
};

describe("submitFailureReport", () => {
  it("posts once and resets only after persistence succeeds", async () => {
    let postCount = 0;
    let resetCount = 0;
    const submitted = await submitFailureReport({
      form: { reset: () => { resetCount += 1; } },
      payload,
      inFlight: { current: false },
      createReport: async () => { postCount += 1; },
    });

    expect(submitted).toBe(true);
    expect(postCount).toBe(1);
    expect(resetCount).toBe(1);
  });

  it("preserves form text when persistence fails", async () => {
    let resetCount = 0;
    const inFlight = { current: false };
    await expect(submitFailureReport({
      form: { reset: () => { resetCount += 1; } },
      payload,
      inFlight,
      createReport: async () => { throw new Error("Network unavailable"); },
    })).rejects.toThrow("Network unavailable");

    expect(resetCount).toBe(0);
    expect(inFlight.current).toBe(false);
  });

  it("rejects a concurrent submission before another POST is sent", async () => {
    let postCount = 0;
    let resolveFirst!: () => void;
    const firstPost = new Promise<void>((resolve) => { resolveFirst = resolve; });
    const inFlight = { current: false };
    const createReport = async () => { postCount += 1; await firstPost; };
    const form = { reset: () => undefined };

    const first = submitFailureReport({ form, payload, inFlight, createReport });
    const second = await submitFailureReport({ form, payload, inFlight, createReport });
    resolveFirst();

    expect(second).toBe(false);
    await expect(first).resolves.toBe(true);
    expect(postCount).toBe(1);
  });
});
