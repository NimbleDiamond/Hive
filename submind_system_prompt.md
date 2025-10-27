# Submind System - Development Brief

## Overview
Build a "Submind" system in Python that simulates a group chat environment where multiple specialized LLM instances discuss, critique, and respond to user prompts. Think of it like a WhatsApp group chat with expert personas.

## Core Concept
- User provides a prompt, question, or idea
- Multiple specialized "subminds" respond to the prompt
- Subminds can see and respond to each other's messages
- Conversation continues until a natural stopping point is reached
- All subminds use OpenRouter API for LLM access

## The Five Subminds

### 1. Doctrinal
- **Focus**: Traditional methods, established practices, historical precedent
- **Role**: Considers how ideas relate to proven approaches and conventional wisdom
- **Perspective**: "How does this align with what's worked before?"

### 2. Analytical
- **Focus**: Scientific approach, data, numbers, evidence
- **Role**: Examines the quantitative and empirical aspects
- **Perspective**: "What does the data tell us?"

### 3. Strategic
- **Focus**: Methods, feasibility, implementation planning
- **Role**: Evaluates practical approaches and viability
- **Perspective**: "How do we actually make this work?"

### 4. Creative
- **Focus**: Unconventional approaches, innovation, novel connections
- **Role**: Explores alternatives and asks "what if?"
- **Perspective**: "What unexpected approach could work here?"

### 5. Skeptic
- **Focus**: Critical analysis, finding weaknesses, challenging assumptions
- **Role**: Devil's advocate, stress-tests ideas
- **Perspective**: "What could go wrong? What are we missing?"

## Technical Requirements

### API Integration
- Use OpenRouter for all LLM calls
- Single API interface for managing multiple model instances
- Consider using different models for different subminds if beneficial

### Architecture
- Group chat/message passing system
- Each submind maintains awareness of conversation history
- Sequential turn-taking (subminds see previous responses before contributing)

### Conversation Flow
1. User submits initial prompt
2. Each submind responds in sequence (or a defined order)
3. After initial round, subminds can respond to each other
4. System detects when conversation should terminate

### Termination Logic
Consider implementing one or more:
- Fixed number of rounds (e.g., 2-3 rounds)
- Detection of consensus or repeated points
- Explicit "done" signals from subminds
- Token/length limits
- Manual user termination option

### Context Management
- Maintain full conversation history for continuity
- Consider summarization if context window becomes an issue
- Each submind should see: original prompt + all previous messages

## Key Design Considerations

### Preventing Issues
- **Groupthink**: The diverse roles (especially Skeptic) should prevent echo chambers
- **Circular arguments**: Implement termination logic to avoid endless loops
- **Redundancy**: System prompts should emphasize each submind's unique perspective

### System Prompts
Each submind needs a clear system prompt defining:
- Their name and core focus
- Their role in the group discussion
- Instruction to build on or challenge others' points
- Instruction to be concise but substantive
- Awareness they're in a multi-agent discussion

### Output Format
- Clear identification of which submind is speaking
- Timestamp or turn number (optional)
- Readable format for following the conversation
- Option to export/save discussions

## Stretch Goals (Optional)
- Async parallel processing for initial responses
- Web interface for easier interaction
- Ability to add/remove subminds dynamically
- Different model assignments per submind
- Conversation export/logging
- Summary generation at end of discussion
- Voting/consensus mechanisms

## Success Criteria
- System successfully routes prompts to all five subminds
- Each submind maintains distinct perspective
- Subminds meaningfully engage with each other's responses
- Conversations reach natural conclusions without manual intervention
- Output is readable and valuable for decision-making

## Notes
- Start simple: get basic group chat working first
- Focus on quality of submind differentiation over technical complexity
- OpenRouter provides flexibility to experiment with different models
- Consider cost implications of multiple LLM calls per interaction