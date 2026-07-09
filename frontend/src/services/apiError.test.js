import { classifyApiError } from './apiError';

describe('classifyApiError', () => {
  test('no response (network/timeout) → network, actionable message', () => {
    const r = classifyApiError({ request: {}, message: 'Network Error' });
    expect(r.kind).toBe('network');
    expect(r.message).toMatch(/connection|reach the server/i);
    expect(r.retryable).toBe(true);
  });

  test('401 → auth (session expired), not retryable in place', () => {
    const r = classifyApiError({ response: { status: 401 } });
    expect(r.kind).toBe('auth');
    expect(r.message).toMatch(/session|sign in/i);
    expect(r.retryable).toBe(false);
  });

  test('423 → locked vault', () => {
    const r = classifyApiError({ response: { status: 423 } });
    expect(r.kind).toBe('locked');
    expect(r.message).toMatch(/lock|unlock/i);
  });

  test('500 with decrypt message → decrypt', () => {
    const r = classifyApiError({
      response: { status: 500, data: { error: 'Unable to decrypt password' } },
    });
    expect(r.kind).toBe('decrypt');
    expect(r.message).not.toMatch(/500|Internal Server Error/);
  });

  test('500 generic → server, retryable', () => {
    const r = classifyApiError({ response: { status: 500, data: {} } });
    expect(r.kind).toBe('server');
    expect(r.retryable).toBe(true);
  });

  test('404 → notfound', () => {
    expect(classifyApiError({ response: { status: 404 } }).kind).toBe('notfound');
  });

  test('429 → ratelimit', () => {
    expect(classifyApiError({ response: { status: 429 } }).kind).toBe('ratelimit');
  });

  test('never leaks a raw server 500 string as the user message', () => {
    const r = classifyApiError({
      response: { status: 500, data: { error: 'psycopg2.OperationalError: FATAL' } },
    });
    expect(r.message).not.toMatch(/psycopg2|FATAL/);
  });
});
