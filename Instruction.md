This file serves as a guidance document for agent operations and **must not be modified under any circumstances**!

**Current directory contents:**
1. **todo.md** - This file specifies the tasks for the agent to execute
2. **memory.md** - This file is for the agent to record its work progress
3. **Tmp/** - This is a directory prepared for the agent

---

### For todo.md:
The agent must sequentially check and complete tasks listed in this file, without modifying any content within todo.md. 

Upon completing each task, the agent **must pause and await review**. During human review, the agent shall perform no actions. After review, humans will add comments following the current task in todo.md, and the agent shall proceed accordingly. Examples:

```
Job 1 xxx
OK move to next mission
```
or
```
Job 1 xxx
Modify xxx implementation
```

---

### For memory.md:
Memory.md serves as the **working context**. The agent must record necessary information, important details, etc., in memory.md. Use the most efficient recording method possible—human readability is not required. The agent may reference this file at any time during work. It must be ensured that if a new agent is initiated, it can quickly switch to the current work context and continue working based on the existing memory.md file.

---

### For the Tmp/ Directory:
The Tmp directory is specifically prepared for the agent. When undertaking a new job, the agent must first conduct experimental and exploratory work within this directory. Work in the main directory is only permitted after the approach has been validated as feasible. And clear the file in the Tmp directory

---

**Final warning**: This file serves as a guidance document for agent operations and **must not be modified under any circumstances**!

