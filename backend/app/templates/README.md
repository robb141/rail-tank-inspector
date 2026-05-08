# DOCX Templates

The copied starter templates live here:

```text
backend/app/templates/osvedcenie_z_template.docx
backend/app/templates/prvotny_zaznam_z_template.docx
```

The MVP uses `docxtpl`, so each DOCX should contain placeholders such as:

```text
{{ certificate_number }}
{{ holder_name }}
{{ holder_street }}
{{ holder_postal_code }}
{{ holder_city }}
{{ holder_country }}
{{ type_approval_number }}
{{ tank_manufacturer_name }}
{{ tank_serial_number }}
{{ year_of_manufacture }}
{{ tank_identification }}
{{ tank_code }}
{{ test_pressure }}
{{ working_pressure }}
{{ calculation_pressure }}
{{ safety_valve_pressure }}
{{ vacuum_valve_pressure }}
{{ capacity_liters }}
{{ cargo_substances }}
{{ special_provisions }}
{{ tank_plate_stamp }}
{{ next_inspection }}
{{ inspection_place }}
{{ inspection_date }}
{{ inspector_name }}
{{ remarks }}
```

For the first MVP, manually edit the copied Word/LibreOffice templates and replace
the visible fields with these placeholders.
