# AURA Phase 1 Product Scope

## 1. Phase 1 Definition

Phase 1 is the first working version of AURA focused on academic support between visually impaired university students and volunteer sighted students.

The product goal is simple:

- a student can request support
- a volunteer can take the request
- both sides can communicate safely
- related materials can be uploaded and shared
- a coordinator can manage and monitor the process

Academic support is the primary focus of Phase 1. Mobility, daily life, and visual description support can exist, but with simpler flows.

## 2. Primary Product Goals

- enable support request creation and tracking
- enable volunteer matching
- enable request-based messaging
- enable accessible material sharing
- give coordinators basic control over users, requests, and interventions

## 3. User Roles

### 3.1 Visually Impaired Student

Can:

- register and log in
- complete a profile
- create support requests
- upload and manage materials related to a request
- review volunteer matches
- message within a request
- close a request and leave feedback

Cannot:

- manage other users
- access unrelated private requests
- moderate the platform

### 3.2 Volunteer Student

Can:

- register and log in
- complete a volunteer profile
- browse open requests
- volunteer for a request or accept coordinator assignment
- message within matched requests
- access materials shared in matched requests
- mark support work as completed

Cannot:

- access unrelated private requests or files
- manage users or system-wide settings

### 3.3 Coordinator

Can:

- review users
- view and manage support requests
- manually match volunteers and students
- intervene in stalled or sensitive cases
- review uploaded materials when necessary
- monitor request statuses and basic activity

Cannot:

- bypass core product rules without traceable action

## 4. Core Request Types

### Priority 1

- academic support
- accessible study material support
- joint studying
- lecture/topic clarification

### Priority 2

- visual description support
- short mobility or wayfinding support

### Priority 3

- daily life support

Phase 1 should be designed around academic support first. Other categories should reuse the same base request flow.

## 5. Main Screens

### Entry and Access

- welcome page
- sign up
- sign in
- password reset
- role selection
- first-time profile completion

### Shared User Area

- dashboard
- notifications
- profile
- account settings
- help page

### Visually Impaired Student Area

- my requests
- create request
- request detail
- matched volunteer view
- request messaging
- my materials
- upload material

### Volunteer Area

- open requests
- request detail
- volunteer action
- my active support items
- request messaging
- shared materials

### Coordinator Area

- coordinator dashboard
- user list and user detail
- request list and request detail
- matching view
- intervention log or activity view

## 6. Core Features by Priority

### Must Have

- sign up, sign in, password reset
- role-based access
- profile creation
- support request creation
- request list and request detail
- request statuses
- volunteer participation flow
- coordinator manual matching
- request-based messaging
- material upload, list, and access
- notifications
- basic coordinator controls

### Should Have

- request filters
- urgency marker
- request history
- simple post-support feedback
- richer material description fields

### Later

- advanced matching logic
- detailed scheduling
- live audio or video sessions
- discussion forums
- gamification
- advanced reporting
- multi-institution management
- AI-assisted conversion or description features

## 7. Key User Flows

### 7.1 Student Onboarding

1. User signs up
2. User selects visually impaired student role
3. User completes profile
4. User lands on dashboard
5. User creates the first support request

### 7.2 Academic Support Request

1. Student starts a new request
2. Student selects academic support category
3. Student enters course, topic, need, urgency, and preferred timing
4. Student uploads related material if needed
5. Student submits request
6. Request becomes available for matching

### 7.3 Volunteer Takes a Request

1. Volunteer signs in
2. Volunteer reviews open requests
3. Volunteer opens request detail
4. Volunteer offers help or accepts assignment
5. Request status changes to matched
6. Messaging becomes active

### 7.4 Coordinator Matches Manually

1. Coordinator reviews unmatched requests
2. Coordinator inspects request need and urgency
3. Coordinator assigns an appropriate volunteer
4. Both sides receive a notification
5. Coordinator can monitor progress

### 7.5 Material Sharing

1. A user uploads a file
2. The user adds description and course context
3. The file is attached to a request or personal material space
4. The matched other party can access it

### 7.6 Closing the Request

1. Student or volunteer marks support as completed
2. Status updates to completed
3. Optional feedback is submitted
4. Request moves to history

## 8. Accessibility Principles for Phase 1

- all critical flows must work with keyboard only
- forms must have explicit labels and clear validation messages
- navigation and heading hierarchy must be consistent
- focus states must be visible and predictable
- color must not be the only carrier of meaning
- statuses, actions, and alerts must be clearly announced
- material upload must require text-based descriptions
- complex tasks must be broken into short, understandable steps

## 9. Out of Scope for Phase 1

- social feed and community features
- advanced scheduling and calendar sync
- live calling or meeting tools
- automated smart matching
- peer rating systems with complex scoring
- institution-level multi-tenant administration
- AI-based document transformation
- collaborative document editing
- deep analytics dashboards

## 10. Smallest Meaningful Working Version

The smallest meaningful version of AURA is achieved when:

- a visually impaired student can register and create an academic support request
- the student can upload relevant study material
- a volunteer student can take the request
- both users can communicate within the request
- a coordinator can intervene and manage the case if needed
