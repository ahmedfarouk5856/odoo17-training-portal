# 🎓 Odoo 17 — Student Training Registration Portal

A fully dynamic public-facing training registration portal built as an Odoo 17 custom module. Students can register for industrial training programs through an AJAX-driven multi-step form without any page reloads.

---

## ✨ Features

- **Student Lookup** — Student enters their University ID → system auto-fills name, phone, national ID, and year level from `op.student`
- **Dynamic Cascading Dropdowns** — Company → Training Program (filtered by year level) → Training Week, all loaded via AJAX
- **Live Seat Capacity** — Week cards show real-time available/full status from `training.weekly.schedule`
- **Year Level Filtering** — Programs are filtered by the student's academic year level (Many2many)
- **Access Control** — Only students registered in the system can submit a registration (backend + frontend validation)
- **Auto Student Creation** — If student doesn't have an `op.student` record, one is created automatically on registration
- **Backend Workflow** — Registrations land as Draft → admin reviews → Confirms with a single click
- **Capacity Enforcement** — Both frontend (pre-check) and backend (`@api.constrains`) block overbooking

---

## 🏗️ Architecture

```
Public Portal (/training/register)
        │
        ▼
TrainingPortalController
        │
        ├── GET  /training/ajax/student     → Lookup op.student by faculty_id
        ├── GET  /training/ajax/programs    → Filter programs by company + level
        ├── GET  /training/ajax/weeks       → Live week slots with capacity
        └── POST /training/register/submit  → Validate + create training.registration
```

---

## 🗄️ Models Used

| Model | Role |
|---|---|
| `masrtech.register.partner` | Training companies (filtered by `is_training=True`) |
| `registrar.partner.training.table` | Training programs with year level Many2many |
| `training.weekly.schedule` | Weekly slots with `max_students`, `registered_count`, `remaining_spots` |
| `op.student` | Student records (OpenEduCat) — looked up by `faculty_id` |
| `training.registration` | Final registration record created on submit |
| `level.year` | Year level records for dynamic dropdown |

---

## ⚙️ Technical Stack

- **Backend:** Odoo 17 ORM, Python controllers, JSON HTTP routes
- **Frontend:** QWeb templates, vanilla JavaScript (no jQuery dependency), AJAX `XMLHttpRequest`
- **UI:** Bootstrap 5, custom CSS (teal/dark theme)
- **Integration:** OpenEduCat (`openeducat_core`) for student management

---

## 📋 Portal Flow

```
1. Student enters University ID
        ↓ AJAX lookup → auto-fills name, phone, national ID, year level
2. Student selects Training Company
        ↓ AJAX → loads programs filtered by student's year level
3. Student selects Training Program
        ↓ AJAX → loads week cards with live capacity
4. Student clicks a week card
        ↓ hidden input captures week ID
5. Student submits
        ↓ Backend validates → creates op.student if needed → creates training.registration (draft)
6. Admin reviews and confirms registration
```

---

## 🚀 Installation

### Prerequisites
- Odoo 17 Enterprise or Community
- OpenEduCat modules installed (`openeducat_core`)
- The following models must exist in your environment:
  - `masrtech.register.partner`
  - `registrar.partner.training.table`
  - `training.weekly.schedule`
  - `training.registration`
  - `level.year`

### Steps

```bash
# 1. Copy module to your addons path
cp -r odoo17_training_portal /path/to/your/addons/

# 2. Update apps list
# Settings → Apps → Update Apps List

# 3. Install the module
# Search for "Student Training Registration Portal" and install

# 4. Add is_training=True to companies you want shown in the portal
# Partners → Training Companies → check "Is Training"
```

---

## 📁 Module Structure

```
odoo17_training_portal/
├── __manifest__.py
├── __init__.py
├── controllers/
│   ├── __init__.py
│   └── training_portal.py          # All HTTP routes + AJAX endpoints
├── models/
│   ├── __init__.py
│   └── training_portal_registration.py   # Portal registration model
├── security/
│   └── ir.model.access.csv
├── views/
│   └── training_portal_registration_views.xml   # Backend tree + form
└── website/
    └── training_registration_template.xml        # Public portal QWeb template
```

---

## 🔧 Key Implementation Details

### AJAX Pattern
All dynamic loading uses plain `XMLHttpRequest` — no jQuery required:
```javascript
function getJSON(url, cb) {
    var x = new XMLHttpRequest();
    x.open('GET', url, true);
    x.onload = function () {
        try { cb(JSON.parse(x.responseText)); } catch(e) { cb([]); }
    };
    x.send();
}
```

### Level Filtering (Python-side)
Many2many domain filtering is done in Python to avoid ORM quirks:
```python
programs = programs.filtered(lambda p: lid in p.level_ids.ids)
```

### CDATA in XML
JavaScript inside QWeb templates uses CDATA to avoid XML parser errors with `&&`:
```xml
<script type="text/javascript">
/* <![CDATA[ */
    // JS code with && operators safely here
/* ]]> */
</script>
```

---

## 👤 Author

**Ahmed Farouk** — Senior Odoo Developer  
Odoo 17 · Python · JavaScript · PostgreSQL · Docker

---

## 📄 License

LGPL-3
