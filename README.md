# Beauty Med Spa Patient Dashboard

Beauty Med Spa is a client of Decoda. They have requested a new patient dashboard to better understand their patients and business operations.

## Background

Beauty Med Spa operates a medical spa offering various aesthetic and wellness services. They currently have patient data stored in JSON files, but they need a modern dashboard to better understand their patient base, track business performance, and make data-driven decisions.

The practice wants to answer questions such as:

- Who are their patients and what are their characteristics?
- How are patients finding the practice?
- What services are most popular?
- How is the business performing financially?
- Which providers are busiest?
- What patterns exist in patient behavior and appointments?

## Task Overview

Build a dashboard displaying existing patients from the `seed_data/` directory and their corresponding relationships. See the full data model definition in [`models.py`](./models.py).

### Data Relationships

The data includes patients, appointments, services, providers, and payment information:

- Patients can have multiple appointments
- Each Appointment can include multiple Services
- Payments are linked to appointments
- Services can be associated with different Providers

Take time to understand these relationships as they will inform your database structure and the insights you can surface.

## Requirements

### Core Implementation

Implement a relational database and load all provided seed data. Create a Python backend API and Next.js frontend.

### Required Pages

1. **Patient Table**

   - A filterable and sortable table showing patients
   - Consider what patient information would be most useful to display to a front desk staff.
   - Think about and add filters, sorts, or groupings that help staff quickly find the patients they're looking for.

2. **Analytics Dashboard**

   - Visualizations and metrics to help them learn about their patients and business performance
   - This is intentionally open-ended, be thoughtful about what information would be genuinely useful to a medical spa owner or manager
   - Consider what metrics, trends, and visualizations would help them understand their business better and make informed decisions
   - Focus on insights that are actionable and relevant to their operations

3. **AI-Ready Architecture** _(During Technical Meeting)_
   - Design your code in such a way that it is conducive to AI-based analytics.
   - During our interview, we will ask you to build a service that allows us to ask arbitrary questions of the data

> **Note:** The client only needs to view this data, so you do not need to implement create, update, or delete functionality.

## Technical Constraints

- **Backend**: Python 3.10+, async Python, async SQLAlchemy
- **Frontend**: Next.js 14, React, TypeScript
- **Database**: PostgreSQL

## Data Notes

- The seed data contains 4,000 patients with associated appointments, services, providers, and payments
- Monetary values are stored in cents (e.g., $100.50 = 10050)
- Consider performance given the data volume—you'll need to think about efficient queries, pagination, and indexing
- Not all appointments have payments—some appointments may be unpaid
- Appointments can have multiple services, each potentially with different providers
- Patient source data indicates how patients found the practice (useful for marketing insights)

## Design Considerations

When building the dashboard, be thoughtful about what you decide to display and what information is useful to the client. Consider:

- What information density is appropriate for each view?
- How can you make the data easy to scan and understand at a glance?
- What visualizations best represent the relationships in the data?
- How can you help the client identify trends, outliers, or opportunities?
- What would be genuinely useful versus what would just be "nice to have"?

Focus on creating a tool that would actually be used day-to-day by the practice staff, not just a technical demonstration.

## Design

The dashboard follows a clean, professional design aesthetic appropriate for a medical spa environment. Key design principles include:

### Visual Design System

- **Color Palette**: A calming, professional color scheme suitable for healthcare environments
- **Typography**: Clear, readable fonts with appropriate hierarchy for data-heavy interfaces
- **Spacing**: Generous whitespace to reduce visual clutter and improve scanability
- **Components**: Consistent, reusable UI components for tables, charts, and navigation

### User Interface Structure

- **Navigation**: Intuitive navigation between Patient Table and Analytics Dashboard views
- **Data Tables**: Clean, scannable tables with clear column headers and row separation
- **Charts & Visualizations**: Clear, accessible charts that effectively communicate business insights
- **Responsive Layout**: Mobile-friendly design that works across different screen sizes

### User Experience Features

- **Loading States**: Visual feedback during data loading operations
- **Error Handling**: Clear, user-friendly error messages when issues occur
- **Filtering & Search**: Intuitive controls for finding and filtering patient data
- **Data Density**: Balanced information density that provides value without overwhelming users

The design prioritizes usability and clarity, ensuring that front desk staff and management can quickly access the information they need to make informed decisions.

*You should follow our design style: https://www.decodahealth.com/*

## Deliverables

- Working, well written and **deployed** application with database, backend, frontend and a publically available link.
- GitHub link to the repository.
- README with any thoughts you have or enhancements you would like to make later.
