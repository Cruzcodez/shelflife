# 4. Handoff

**Date:**
**Built by:**
**Handed to:**

Write this at the end, for the person who gets this after you. That might be a customer, a teammate, or you in eight months with no memory of any of it.

Assume they know their own job but nothing about this project. Explain the parts that are specific to what you built. Don't explain what a Lambda function is, do explain why there are two of them.

---

## What this is

Two or three sentences. What it does, what question it was answering.

> 

## What it doesn't do

Straight from the out-of-scope list in `03-scope.md`. Repeat it here, because this is the document people actually keep.

- 
- 

## This is not production ready

Read this part before you deploy anything.

This was built to answer a question, not to be run for real. Here's what's missing and what it would take to fix. Be specific. "Needs hardening" tells nobody anything.

| What's missing | Why it matters | Roughly what it takes |
| --- | --- | --- |
|  |  |  |
|  |  |  |

Common ones worth checking before you say the list is done: authentication, input validation, error handling, logging and alerting, secrets management, backups, rate limiting, and what happens when it gets more traffic than one person clicking around.

If you deploy this as-is and something goes wrong, the answer is in this table.

## Running it

Exact commands. Assume they're starting from a fresh machine and a fresh clone.

```bash
# prerequisites

# install

# configure

# run
```

### Things it needs to exist

Accounts, credentials, permissions, network access. Say what each one is for, and say what to do if they don't have it.

- 

## How it's put together

Enough for someone to find their way around. A diagram beats a paragraph, but a paragraph beats nothing.

> 

### Where to change things

The three or four most likely things someone will want to modify, and where to go.

| If you want to change... | Look in... |
| --- | --- |
|  |  |

## Tearing it down

**Don't skip this.**

If this spun up cloud resources, they're costing money right now, and they'll keep costing money long after everyone stops thinking about this project. Write down how to remove all of it.

```bash
# teardown
```

### Manual cleanup

Anything the teardown script won't catch. Be thorough, this is where the surprise bills live.

- [ ] IAM users, roles and access keys created for this
- [ ] Storage buckets, including versioned objects
- [ ] DNS records
- [ ] Certificates
- [ ] API keys issued by third party services
- [ ] Scheduled jobs
- [ ] Anything created by hand in a console

Deleting the resources does not delete the credentials that were made to manage them. An access key with nothing left to manage is still a live access key.

## What we learned

The part people skip, and the part that's worth the most later.

What surprised you. What you'd do differently. What you tried that didn't work, so nobody repeats it. What the original question turned out to be hiding.

> 

## Open questions

Things still unresolved, so whoever picks this up doesn't think they're the first to notice.

- 

## Who to ask

> 

---

## Prompt for your AI assistant

This one reviews your handoff by trying to use it, which is a different job from writing it.

```
Here's a handoff document for a proof of concept:

[paste 04-handoff.md]

And here's the repository structure:

[paste output of: find . -type f -not -path './.git/*' | sort]

Read it as someone who has just inherited this project, knows their way
around software generally, and knows nothing about this specific thing.

Tell me:
- Where would I get stuck trying to run this from scratch? Name the exact step.
- What does it assume I already know that it didn't explain?
- What's in the repo that the handoff never mentions?
- Is the teardown section actually complete, given what's in the repo? What
  would still be running and costing money if I followed it exactly?
- Does "not production ready" say specific things, or is it hand-waving?

Don't be polite about it. A handoff that reads fine and leaves someone stuck
is worse than no handoff, because they'll waste a day before asking.
```
