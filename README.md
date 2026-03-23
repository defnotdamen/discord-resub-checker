# Discord Nitro Resub Checker

A multithreaded tool to check Discord tokens for Nitro subscription status and resub eligibility.

## What it does

- Checks if tokens have active Nitro subscriptions
- Identifies tokens in grace/resub period (will auto-renew)
- Identifies tokens with upcoming resub periods
- Sorts tokens into categorized output files

## Setup

1. Add tokens to `tokens.txt` (format: `email:pass:token`)
2. Add proxies to `proxies.txt` (format: `ip:port` or `user:pass@ip:port`)
3. Run: `python main.py`
4. Enter thread count when prompted

## Output

Results saved to `Output/<timestamp>/`:

| File | Description |
|------|-------------|
| `resub_period_ending_in_X_days.txt` | Currently in grace period, X days until resub expires |
| `resub_period_will_start_in_X_days.txt` | Active sub, will enter resub period in X days |
| `no_resub_period.txt` | No active subscription or resub eligibility |

buy tokens from https://boostsync.cc/ 🚀


## Notes

- Proxies are optional but recommended for bulk checking
- Auto-retries up to 3 times on proxy failures
- Thread-safe file writes
