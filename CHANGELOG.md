# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project does not yet follow semantic versioning (still in development).

## [Unreleased]

### Added
- (pending...)

## [1.1.0] – Extended Personal Finance Features

- **Income tracking system**:
  - Introduced new `incomes` table with support for amount, source, category, notes, and timestamps.
  - CRUD operations for income entries (create, read, update, delete).
  - API routes under `/incomes` with pagination and optional filtering for listing incomes.
- **Financial overview (/summary/overview)**:
  - Now returns both total income and total expenses.
  - Calculates **total income**, **total expenses** and **net balance** (income – expenses).
  - Supports different period options (weekly, monthly, yearly) with optional grouping extensions in progress to compare trends.
- **Grouped overview (/summary/overview)**:
  - Added optional group_by parameter to /summary/overview.
  - Supports grouped financial snapshots:\
  •GET /summary/overview?period=monthly&group_by=weekly\
  •GET /summary/overview?period=yearly&group_by=quarterly\
  •And more (weekly, monthly, quarterly, half-yearly).
- **Swagger UI documentation** for new Income endpoints and updated overview route.

### Improved
- Consistent timestamp handling across all models (UTC-aware).
- Unified normalization for text fields (`source`, `category`) across schemas and CRUD.
- Tags metadata consistency to avoid duplicate groups in Swagger.
- Enhanced testability of financial metrics (verified expense vs. income calculations).


## [1.0.0] – First production release

### Added
- User registration and login functionality
- Budget creation and category-based tracking
- Expense logging for user-defined budgets
- Support for period-based and category-based expense views
- Budget alert system based on usage thresholds:
  - 50% (half-limit)
  - 80–99% (near-limit)
  - 100%+ (limit-exceeded)
- HTML-based email templates using Jinja (`email_alert.html`)
- Email alert notifications for budget usage via SendGrid
- Dynamic username inclusion and year rendering in email templates
- Enhanced email layout with clear visual alert icons and structure
- **Spending summary endpoint**:
  - Supports optional category filtering
  - Groups and aggregates expenses by time period (`weekly`, `monthly`, `yearly`)
  - Real-time summary calculation based on `created_at` timestamps
  - Returns structured data using Pydantic response models
- Deployment to Render with PostgreSQL database hosting
- Environment-based database switching (local vs. production)
- Alembic-based migration system integrated into deployment process

### Improved
- Overall alert messaging structure and logic
- Email deliverability (successfully sending authenticated emails via SMTP/SendGrid)
- Reduced risk of alert duplication through alert log checks
- Normalized category and period input to avoid mismatches in queries
- Deployment stability via environment-specific configurations
- Password hashing and validation robustness (bcrypt backend ensured)
- Project structure for scalability and clean separation of concerns

### Fixed
- Resolved migration failures due to missing table metadata in production
- Handled missing dependencies (`email-validator`, `python-multipart`, `bcrypt`) during deployment
- Corrected Alembic import and model registration issues preventing database syncing
- Adjusted internal vs. external database URL use to ensure secure production access

---

## [0.1.0] – Project initialized

### Added
- Project scaffolding and development environment setup