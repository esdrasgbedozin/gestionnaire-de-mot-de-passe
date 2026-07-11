import { mapWithConcurrency } from "./concurrency";

const flush = () => new Promise((r) => setTimeout(r, 0));

describe("mapWithConcurrency", () => {
  test("preserves result order regardless of completion order", async () => {
    const out = await mapWithConcurrency(
      [10, 5, 1],
      3,
      (n) => new Promise((res) => setTimeout(() => res(n * 2), n)),
    );
    expect(out).toEqual([20, 10, 2]); // order of INPUT, not of completion
  });

  test("never runs more than `limit` tasks in flight", async () => {
    let inFlight = 0;
    let maxInFlight = 0;
    const items = Array.from({ length: 20 }, (_, i) => i);
    await mapWithConcurrency(items, 5, async () => {
      inFlight += 1;
      maxInFlight = Math.max(maxInFlight, inFlight);
      await flush();
      inFlight -= 1;
    });
    expect(maxInFlight).toBeLessThanOrEqual(5);
    expect(maxInFlight).toBeGreaterThan(1); // actually parallel, not serial
  });

  test("reports progress once per item, ending at total", async () => {
    const seen = [];
    await mapWithConcurrency(
      [1, 2, 3, 4],
      2,
      async (n) => n,
      (done) => seen.push(done),
    );
    expect(seen).toHaveLength(4);
    expect(Math.max(...seen)).toBe(4);
  });

  test("empty input resolves to empty array", async () => {
    expect(await mapWithConcurrency([], 5, async (n) => n)).toEqual([]);
  });
});
