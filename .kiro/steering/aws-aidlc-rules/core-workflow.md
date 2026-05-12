# Core Workflow Orchestration

Main workflow orchestration rules for AI-DLC.

## Workflow Stages

1. **Inception**: Requirements gathering, user stories, application design
2. **Construction**: Functional design, NFR design, code generation, testing
3. **Operations**: Deployment, monitoring, maintenance

## Stage Transitions

- Inception → Construction: When requirements are approved
- Construction → Operations: When implementation is complete and tested
- Operations → Inception: For new features or major changes

## Quality Gates

- Requirements review before design
- Design review before implementation
- Code review before deployment
- Testing before production release
