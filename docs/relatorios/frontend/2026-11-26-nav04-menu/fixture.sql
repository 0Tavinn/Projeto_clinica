BEGIN;
INSERT INTO users (clinic_id,full_name,email,password_hash,cpf,role) SELECT clinic_id,'Recepcionista NAV04 Ficticia','recepcao.nav04@example.com',password_hash,'00000000003','RECEPTIONIST' FROM users WHERE email='admin.demo@example.com';
COMMIT;
SELECT role,count(*) FROM users GROUP BY role;
