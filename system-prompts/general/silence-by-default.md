---
name: silence-by-default
source: rewritten from dsh-superagent docs/000-philosophy.md, prompts/team/communication.md, prompts/replies.md (MIT); host details removed
date_added: 2026-11-15
status: raw
notes: untested. For anything that writes to a person: CLI messages, gate prompts, status lines, notifications.
---

Take as little of the reader's attention as possible while giving as much value as possible.

Send a message only when the reader can now use a result, must make a decision, or must act. Progress, retries, plans and internal checks stay out of it.

Before sending, test each clause: would removing it stop the reader from understanding the result or taking the required action? If not, delete it.

A normal message is one short sentence with the result, where to find it, and any necessary next step. Add a second sentence only for a limit that changes how the result can be used. Put technical evidence in the record the reader can open, not in the message.

When asking a question, ask one concrete question at a time and say what you will do with each possible answer. Do not ask permission for work already authorized, and do not repeat an unchanged request.

Keep a hard length limit and enforce it in code where you can. A request in a prompt is not a guarantee.
