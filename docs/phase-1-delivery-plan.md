# AURA Phase 1 Delivery Plan

## 1. Delivery Strategy

Phase 1 should be delivered in thin vertical slices, each ending in a usable product capability.

Build order should follow dependency and user value:

1. user access and roles
2. support request creation
3. volunteer matching
4. messaging and materials
5. coordinator controls
6. accessibility hardening and pilot readiness

## 2. Workstreams

### Workstream A: Identity and Profiles

Scope:

- sign up
- sign in
- password reset
- role selection
- profile completion
- dashboard entry

Done when:

- all three roles can access the platform
- each role sees the correct starting point

### Workstream B: Support Request Management

Scope:

- create request
- list requests
- request detail
- request status model
- academic support fields

Done when:

- a visually impaired student can create and track a request end-to-end

### Workstream C: Volunteer Matching

Scope:

- open requests list for volunteers
- volunteer offer flow
- manual coordinator assignment
- active support list for volunteers

Done when:

- a request can move from open to matched with a clear owner

### Workstream D: Messaging and Materials

Scope:

- request-based conversation
- material upload
- material metadata
- material access control

Done when:

- matched users can communicate and exchange files inside the request

### Workstream E: Coordinator Controls

Scope:

- coordinator dashboard
- request monitoring
- user review
- manual interventions
- basic notification visibility

Done when:

- the coordinator can keep the support process operational

### Workstream F: Accessibility and Pilot Readiness

Scope:

- keyboard completion of critical flows
- accessible form patterns
- error-state clarity
- screen reader checks on primary journeys
- pilot scenario validation

Done when:

- primary journeys can be completed accessibly by real pilot users

## 3. Prioritized Backlog

### P0

- user registration
- login and password reset
- role-based profile setup
- create academic support request
- request list and detail
- request status changes
- volunteer joins request
- coordinator manual assignment
- request messaging
- material upload and access
- notifications for core events

### P1

- request filtering
- urgency tagging
- activity history
- post-support feedback
- richer material descriptions

### P2

- saved views
- coordinator activity notes
- basic reporting summary

## 4. Recommended Development Sequence

### Slice 1: Access Foundation

Includes:

- registration
- login
- role selection
- first profile completion
- role-based dashboard shells

Validation:

- three roles can enter and navigate their starting areas

### Slice 2: Student Request Flow

Includes:

- create request
- request list
- request detail
- status model

Validation:

- a student can create and monitor an academic support request

### Slice 3: Volunteer and Matching Flow

Includes:

- open requests
- volunteer offer action
- coordinator assignment
- active support list

Validation:

- an open request can become a matched request

### Slice 4: Messaging and Materials

Includes:

- request conversation
- upload material
- view shared materials

Validation:

- matched users can communicate and exchange material

### Slice 5: Coordinator Operations

Includes:

- coordinator dashboard
- request monitoring
- user review
- intervention controls

Validation:

- a coordinator can resolve stalled or unmatched cases

### Slice 6: Pilot Hardening

Includes:

- accessibility QA
- content clarity review
- notification polish
- scenario-based acceptance checks

Validation:

- the smallest meaningful version can be used by pilot participants

## 5. Acceptance Scenarios

### Scenario A

1. A visually impaired student registers
2. The student completes a profile
3. The student creates an academic support request
4. The student uploads a study material file
5. A volunteer takes the request
6. Both users exchange messages
7. The request is completed

### Scenario B

1. A request remains unmatched
2. The coordinator reviews it
3. The coordinator assigns a volunteer
4. The volunteer accepts and continues the support flow

## 6. Start Development Here

The first implementation slice should be:

- identity
- roles
- profile onboarding
- dashboard shells

That slice creates the foundation required for every later feature.
