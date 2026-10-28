-- Verificação somente de leitura após reiniciar o PostgreSQL descartável.
BEGIN READ ONLY;
DO $verify$
BEGIN
    IF current_database() NOT IN (
        'lumina_acl_new_20261024', 'lumina_acl_upgrade_20261024'
    ) THEN
        RAISE EXCEPTION 'Verificação permitida apenas nos bancos descartáveis identificados';
    END IF;
    IF (SELECT count(*) FROM clinics) <> 1
       OR (SELECT count(*) FROM users) <> 2
       OR (SELECT count(*) FROM dentists) <> 2
       OR (SELECT count(*) FROM patients) <> 2
       OR (SELECT count(*) FROM appointments) <> 3
       OR (SELECT count(*) FROM medical_records) <> 1
       OR (SELECT count(*) FROM clinical_evolutions) <> 1
       OR (SELECT count(*) FROM clinical_access_grants) <> 3 THEN
        RAISE EXCEPTION 'Dados fictícios não foram preservados após reinício';
    END IF;
    IF (SELECT count(*) FROM clinical_access_grants AS g
        JOIN appointments AS a ON a.id = g.appointment_id
        JOIN patients AS p ON p.id = g.patient_id
        JOIN dentists AS d ON d.id = g.dentist_id
        WHERE p.medical_record_number = 'ACL-FAKE-1'
          AND d.cro_number = 'ACL-FAKE-A') <> 2 THEN
        RAISE EXCEPTION 'Múltiplas origens da mesma dupla foram perdidas';
    END IF;
    IF EXISTS (
        SELECT 1 FROM clinical_access_grants AS g
        JOIN appointments AS a ON a.id = g.appointment_id
        WHERE (g.clinic_id, g.patient_id, g.dentist_id)
           IS DISTINCT FROM (a.clinic_id, a.patient_id, a.dentist_id)
           OR g.granted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Origem ou data da concessão divergente';
    END IF;
    IF (SELECT status FROM appointments WHERE notes = 'Consulta fictícia A') <> 'COMPLETED'
       OR (SELECT status FROM appointments WHERE notes = 'Consulta fictícia B') <> 'CANCELED'
       OR (SELECT status FROM appointments WHERE notes = 'Consulta fictícia C') <> 'NO_SHOW'
       OR NOT EXISTS (SELECT 1 FROM medical_records
                      WHERE general_notes = 'Observação fictícia anterior')
       OR NOT EXISTS (SELECT 1 FROM clinical_evolutions
                      WHERE description = 'Evolução fictícia anterior') THEN
        RAISE EXCEPTION 'Estados ou dados clínicos anteriores divergentes';
    END IF;
END;
$verify$;
ROLLBACK;
