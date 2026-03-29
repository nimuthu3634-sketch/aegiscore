import { cn } from "@/lib/utils";
import { formatDate, scoreTone, toTitleCase } from "@/lib/format";

describe("format helpers", () => {
  it("merges class names", () => {
    expect(cn("rounded", "px-4", undefined, false && "hidden")).toContain("rounded");
  });

  it("formats dates and score tones", () => {
    expect(formatDate("2026-03-29T04:10:00Z")).toContain("Mar");
    expect(scoreTone(90)).toBe("critical");
    expect(toTitleCase("has_network_signal")).toBe("Has Network Signal");
  });
});
