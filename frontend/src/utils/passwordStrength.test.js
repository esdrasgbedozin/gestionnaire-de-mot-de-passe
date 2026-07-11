import {
  evaluateStrength,
  strengthFromBackendScore,
  meetsStrengthRequirement,
} from './passwordStrength';

describe('evaluateStrength (single zxcvbn-backed engine)', () => {
  test('empty password → None / gray, score -1', () => {
    const s = evaluateStrength('');
    expect(s.label).toBe('None');
    expect(s.color).toBe('gray');
    expect(s.score).toBe(-1);
    expect(s.percent).toBe(0);
  });

  test('a very common password scores low (red) and is not "requirement met"', () => {
    const s = evaluateStrength('123456');
    expect(s.score).toBeLessThanOrEqual(1);
    expect(s.color).toBe('red');
    expect(meetsStrengthRequirement('123456')).toBe(false);
  });

  test('a truly random password scores at the top (green) and meets the requirement', () => {
    const s = evaluateStrength('X#9$mP2!vR8@nQ5z');
    expect(s.score).toBe(4);
    expect(s.color).toBe('green');
    expect(s.label).toBe('Very strong');
    expect(meetsStrengthRequirement('X#9$mP2!vR8@nQ5z')).toBe(true);
  });

  test('DISCRIMINANT: "looks complex but weak" scores strictly below a true random', () => {
    // Passw0rd1234! a l'air complexe (4 classes, 13 car.) mais est devinable.
    const looksComplex = evaluateStrength('Passw0rd1234!').score;
    const trulyRandom = evaluateStrength('X#9$mP2!vR8@nQ5z').score;
    expect(looksComplex).toBeLessThan(trulyRandom);
  });

  test('percent maps score 0..4 → 20..100', () => {
    expect(evaluateStrength('X#9$mP2!vR8@nQ5z').percent).toBe(100);
    expect(evaluateStrength('123456').percent).toBeLessThanOrEqual(40);
  });
});

describe('strengthFromBackendScore (backend 1-5 → same scale)', () => {
  test('1 → Very weak (red), 3 → Fair (yellow), 5 → Very strong (green)', () => {
    expect(strengthFromBackendScore(1).label).toBe('Very weak');
    expect(strengthFromBackendScore(1).color).toBe('red');
    expect(strengthFromBackendScore(3).label).toBe('Fair');
    expect(strengthFromBackendScore(3).color).toBe('yellow');
    expect(strengthFromBackendScore(5).label).toBe('Very strong');
    expect(strengthFromBackendScore(5).color).toBe('green');
  });

  test('out-of-range / missing backend score is clamped, never throws', () => {
    expect(() => strengthFromBackendScore(undefined)).not.toThrow();
    expect(strengthFromBackendScore(99).score).toBe(4);
    expect(strengthFromBackendScore(0).score).toBe(0);
  });
});
