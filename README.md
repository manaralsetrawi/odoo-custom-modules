# NCST ERP Workflow Enhancement System

## Description
This project contains the custom Odoo modules developed for the **NCST ERP Workflow Enhancement System**, a customized **Odoo 18 Community** solution created for **Nasser Centre for Science and Technology (NCST)**.

The purpose of the project is to improve the existing ERP environment through modular customization instead of replacing the system completely. The custom modules extend standard Odoo functionality to better support real organizational workflows in procurement, finance, CRM, user management, budget and expense handling, and AI-supported features.

The repository exists to provide the implementation logic behind the customized ERP solution. It is intended for technical users who want to review, install, maintain, or extend the custom modules developed for the NCST environment.

---

## Features

- Customized **HR management workflow**
  - Attendance management using standard Odoo configuration
  - Time off request creation by employees
  - Sequential time off approval workflow (Supervisor → HR)
  - Automatic leave allocation for annual leave and sick leave
  - Leave rejection handling with reason tracking
  - Public holidays and leave types configuration

- Customized **procurement execution workflow**
  - Purchase request linkage
  - Quotation handling and evaluation
  - Vendor recommendation
  - Financial approval routing
  - Budget reservation integration
  - Vendor acknowledgment
  - Receipt compliance confirmation
  - Vendor bill verification
  - Payment tracking
  - Procurement closure

- Customized **purchase request workflow**
  - Purchase request creation by teachers and administrative staff
  - Teacher request flow (Coordinator → Academic Principal approval)
  - Administrative staff request flow (Department Director approval)
  - Purchase request line management with products, quantity, and estimated prices
  - Automatic purchase request reference generation
  - Role-based access control for request creation, editing, and deletion
  - Purchase request rejection with reason logging
  - Budget verification before final approval

- Customized **finance workflow**
  - Invoice review workflow
  - Approval and rejection handling
  - Exception-control checks
  - Vendor bill verification
  - Dashboard visibility
  - Payment tracking

- Customized **budget and expense management**
  - General yearly budget management
  - Department budget allocation workflow
  - Budget reservation management
  - Budget balance validation
  - Expense request workflow
  - Manager and finance approval for expenses
  - Expense rejection with reason tracking
  - Finance dashboard and reporting
  - Finance KPI calculations

- Customized **CRM workflow**
  - Project request intake
  - Custom workflow stages
  - Validation logic
  - Proposal handling
  - Approval and rejection flow
  - Follow-up activities and reminders
  - Email logging management
  - Sending emails from CRM records
  - Client segmentation management
  - Project type management
  - Project features management
  - Project teams management
  - Automatic project team assignment
  - Employee availability validation to prevent overlapping project assignments
  - Leads / project request dashboard

- **User management automation**
  - Automatic email generation
  - Automatic login generation
  - Duplicate-name validation
  - Default password logic
  - Safer default access setup

- **AI-supported features**
  - Assistant chatbot integration
  - Project proposal PDF upload
  - Automatic proposal summary generation

- Supporting modules for:
  - budget management
  - expense management
  - leave workflow support
  - backend UI enhancement

---

## Technologies Used
- **ERP Platform:** Odoo 18 Community Edition
- **Backend Language:** Python
- **Frontend / Views:** XML / QWeb
- **Client-side Scripting:** JavaScript
- **Styling:** SCSS
- **Database:** PostgreSQL
- **PDF Processing:** PyPDF
- **AI Integration:** OpenAI API
- **Development Tools:** GitHub, VS Code

---

## Installation
Follow these steps to use the modules in a local Odoo environment.

1. **Prepare an Odoo 18 Community environment**
   - Make sure Odoo 18 Community is installed and working correctly.
   - Make sure PostgreSQL is installed and configured.

2. **Add the custom modules**
   - Copy the required module folders from this repository into your Odoo custom addons path.

3. **Check module dependencies**
   - Open each module’s `__manifest__.py` file.
   - Make sure all dependent standard or custom modules are installed before installing the module.

4. **Update the addons path**
   - Add the repository module path to your Odoo addons configuration.

5. **Update the apps list**
   - Start Odoo.
   - Open the Apps menu.
   - Update the apps list so Odoo detects the new modules.

6. **Install the required modules**
   - Install the needed modules from the Odoo Apps interface, or upgrade them if they already exist in the database.

7. **Assign users and security roles**
   - After installation, configure users and assign the appropriate groups depending on the workflow being used.

### Important Note
Some modules depend on other custom modules in this repository. Installation order may matter, especially for:
- procurement modules
- budget-related modules
- CRM workflow modules
- AI-related modules

Always review each module manifest before installation.

---

## Usage
The modules in this repository are used inside the Odoo backend after installation.

### General Usage Flow
- Users log in to Odoo with the appropriate role.
- Each module adds or extends menus, forms, actions, dashboards, workflow buttons, validations, and security rules.
- Users interact with the customized workflows based on their assigned permissions.

### Example Usage Areas

#### Procurement
- Link RFQs or Purchase Orders to approved Purchase Requests
- evaluate quotations
- select recommended vendors
- send records for financial approval
- record vendor acknowledgment
- confirm receipt compliance
- verify vendor bills
- track payment and close procurement

#### Finance
- submit invoices for review
- approve or reject invoices
- check finance exceptions
- verify vendor bills
- review finance dashboard indicators

#### CRM
- manage project request workflow
- move records through custom stages
- validate proposal requirements
- track follow-up actions and reminders

#### User Management
- create internal users with auto-generated email and login
- apply safer default access
- reduce manual account setup effort

#### AI Features
- use the assistant chatbot inside Odoo
- upload project proposal PDFs
- generate automatic proposal summaries

---

## Project Structure
This repository mainly contains the `custom_addons` directory, which stores the custom-developed Odoo modules.

```bash
custom_addons/
├── .vscode/
├── backend_theme/
├── crm_project_request_intake/
├── crm_workflow_custom/
├── finance_review_workflow/
├── hr_employee_auto_leave_allocation/
├── hr_holidays_sequential_approval/
├── ncst_ai_chatbot/
├── ncst_budget_management/
├── ncst_expense_management/
├── ncst_website_request/
├── purchase_execution_workflow/
├── purchase_request/
├── purchase_request_workflow/
└── user_email_autofill/
