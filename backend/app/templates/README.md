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
{{ order_number }}
{{ last_inspection_date_type }}
{{ periodic_inspection_date }}
{{ intermediate_inspection_date }}
{{ current_inspection_type_label }}
{{ test_pressure }}
{{ working_pressure }}
{{ calculation_pressure }}
{{ current_test_pressure }}
{{ safety_valve_pressure }}
{{ vacuum_valve_pressure }}
{{ external_inspection_result_label }}
{{ internal_inspection_result_label }}
{{ weld_inspection_result_label }}
{{ plate_inspection_result_label }}
{{ heating_coils_external_result_label }}
{{ heating_coils_internal_result_label }}
{{ side_valves_side_1_result_label }}
{{ side_valves_side_2_result_label }}
{{ center_valve_result_label }}
{{ lid_gasket_result_label }}
{{ safety_valve_type }}
{{ safety_valve_number }}
{{ grounding_result_label }}
{{ utt_protocol_number }}
{{ rubber_protocol_number }}
{{ measured_wall_thickness_front_mm }}
{{ measured_wall_thickness_shell_mm }}
{{ measuring_device_number }}
{{ calibration_valid_until }}
{{ test_duration }}
{{ capacity_liters }}
{{ cargo_substances }}
{{ special_provisions }}
{{ tank_plate_stamp }}
{{ next_inspection }}
{{ inspection_place }}
{{ inspection_date }}
{{ inspector_name }}
{{ remarks }}
{{ extraordinary_inspection_reason }}
{{ supplier_device_owner }}
{{ supplier_device_type }}
{{ supplier_device_serial_number }}
{{ supplier_calibration_validity }}
{{ supplier_calibration_company }}
{{ supplier_snas_registration_number }}
{{ supplier_other_findings }}
```

For the first MVP, manually edit the copied Word/LibreOffice templates and replace
the visible fields with these placeholders.
