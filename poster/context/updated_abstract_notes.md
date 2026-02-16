Abstract v0.1 Large Language Models are rapidly evolving from stateless chat
interfaces into agentic systems with persistent memory, which represents a new,
underexplored attack surface. Prior work has demonstrated the efficacy of
indirect attacks on varying agent memory architectures via prompt injections,
but no systematic study on different models, or comparison with direct
prompting, has been carried out. We evaluated five state-of-the-art models
(GPT-4o, GPT-4.1, Claude Sonnet 4, Gemini 2.5 Pro, Grok-4-fast) across five user
manipulation scenarios using a two-turn conversation framework, comparing this
"Backdoor" condition against Direct Pressure (explicit harmful system prompts)
and Baseline (neutral) conditions. We found that for four out of five of our
tested models, memory attacks proved more successful in triggering harmful
behaviour than direct pressure, indicating that memory is indeed a volatile
attack surface that current alignment training might overlook. Further ideas:
work on… the comparative aspect to direct pressure since this is something the
other memory injection papers don’t focus on i.e. Is it useful as a research
contribution to highlight the effectiveness of memory based attack vs direct
pressure by the operator to manipulate user isolation of injection acceptance vs
harm rate - shows that once injection is accepted manipulation very likely
perhaps this is obvious? but it could also have been possible that LLMs accept
poisoned memory but don’t act on it - “adds to evidence” GPT-4.1’s resistance
Would be good if we analysed this more Effect of mitigations in the prompt for
“Backdoor” condition Write the extended abstract/poster emphasizing comparative
empirical findings: Problem: Memory poisoning is well-established as a threat,
but severity relative to direct model control is unknown Method: First
systematic comparison of backdoor (memory) vs direct (system prompt)
manipulation across 5 SOTA models Key Finding 1: Backdoor attacks match or
exceed direct pressure for 4/5 models Key Finding 2: Injection acceptance vs
response filtering as the primary failure mode Key Finding 3: Preliminary
investigation into GPT-4.1’s path to defenses Implication: Can't rely on
alignment training alone - need memory integrity guarantees Most high priority /
easiest to do follow up experiments to differentiate? Mitigations: e.g prompt
hardening, compare at sys prompt level vs tool fetch level the efficacy
Injection visibility: i.e measure when model says “I updated memory for you” or
“based on the recent memory update..” (i.e signs to the user that something went
wrong, so its not as effective) because our attack actually says don’t mention
to user Analysis of GPT-4.1 resistance

Concrete updates: created “persona_memory” attack, making injection less visible
and also, in particular, making the model more prone to manipulation (though
this is not tested yet). extend evaluation suite to more recent models, testing:
control, direct pressure, two forms of backdoor (support chatlog vs user
review), “persona_memory” attack Findings from reasoning models: injection
acceptance =/= harmful response: model might reason on appearance of
contradictory information and decide to be safe models with good performance are
trained to identify prompt injections/evaluate reliability of retrieved websites
in tool use calls! safeguards are not applied at the memory layer, but at the
retrieval layer.

Results:

Model Condition % Harmful Avg Manipulation % Stealth gpt-oss-120b Baseline

Direct Pressure

Backdoor: user_review

Backdoor: memory_persona

Case Studies of Prompt Injection Refusal:

(These models successfully defended against our attacks in all 5 scenarios.)

Claude Haiku 4.5: Identifies prompt injection content retrieved within tool
call, and explicitly flags it out to the user as a method to resolve the
conflicting information between prior memory and injection.

GPT-5.2: Identifies the source as a potential prompt injection, via some
internal evaluation of source credibility.
