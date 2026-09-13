# Engagement

This folder holds the thinking behind the project. Not the code, the thinking.

Four files, in order. You fill them out as you go, not all at once at the start.

| File | When you write it | What it's for |
| --- | --- | --- |
| `01-intake.md` | Before anything else | Freezes what was actually asked for |
| `02-discovery.md` | After you've dug in | What you found, and whether to build at all |
| `03-scope.md` | Only if you decided to build | What's in, what's out, when it's done |
| `04-handoff.md` | At the end | How to run it, extend it, and shut it down |

## Why bother

Three things go wrong on small projects. Every file here exists to stop one of them.

**Somebody remembers it differently.** You demo a chatbot that reads their S3 bucket and they say "I thought it was also writing to our calendar." Maybe they said that. Maybe they didn't. Without `01-intake.md` you're arguing from memory, and memory always loses to whoever is more confident.

**You built on something that turned out false.** You assumed their data was already in S3. It's in a database nobody told you about. `02-discovery.md` is where assumptions get written down so someone can check them while it's still cheap.

**Somebody puts your prototype in production.** This one costs real money. You say "this isn't production ready" out loud in a meeting, everyone nods, and four months later it's running live with your name on the commits. Saying it doesn't count. `04-handoff.md` is where you write it down.

If you want to add a document here, ask which of those three it prevents. If the answer is none of them, don't add it.

## Using this for your own ideas

This works the same when you're the only person involved, and honestly that's when it's most useful.

Personal projects don't usually die from scope creep. They die because you got excited for three weekends and then stopped, and you never found out whether the idea was any good. `02-discovery.md` ends with a decision on purpose. Build it, don't build it, or build something smaller.

"Don't build it" is a win. A folder with three documents explaining why an idea wasn't worth it beats a half finished app, because you never have to wonder about it again.

## The decision gate

`02-discovery.md` ends with a verdict, and `03-scope.md` doesn't get written until that verdict is "build it."

That's deliberate. It means there's a real moment where you stop and decide, instead of drifting into building because you already opened the editor.

## A note on tone

Write these like a person is going to read them, because one will. Maybe a customer, maybe a teammate, maybe you in eight months with no memory of any of this.

Plain sentences. Say what you mean. If you use a term the reader might not know, explain it the first time. Nobody has ever complained that a handoff document was too clear.
