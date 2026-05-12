-- Импорт QR-токенов для raffle.db
-- Безопасно для повторного запуска: используется INSERT OR IGNORE

INSERT OR IGNORE INTO qr_tokens (token, issued_for_receipt, issued_at, active_for_next_stage)
VALUES
('QR-2OY01A2G7U4', 'RCP-0001', datetime('now'), 1),
('QR-1IDRWZMIXOS', 'RCP-0002', datetime('now'), 1),
('QR-DHFKJO6CKY4', 'RCP-0003', datetime('now'), 1),
('QR-KY2PQWSFWSI', 'RCP-0004', datetime('now'), 1),
('QR-WWO_GO0QC0U', 'RCP-0005', datetime('now'), 1),
('QR-SJJKPVDJLTC', 'RCP-0006', datetime('now'), 1),
('QR-EK-WI5EQLVK', 'RCP-0007', datetime('now'), 1),
('QR-1LV0QZDL4QW', 'RCP-0008', datetime('now'), 1),
('QR-E9PS_UJUNQ0', 'RCP-0009', datetime('now'), 1),
('QR-IISJVWDBKYO', 'RCP-0010', datetime('now'), 1),
('QR-VSUTPLBAIXW', 'RCP-0011', datetime('now'), 1),
('QR-NYEXJ0QAHHI', 'RCP-0012', datetime('now'), 1),
('QR-WW-HZTYSEGW', 'RCP-0013', datetime('now'), 1),
('QR-B_A23PH5HXS', 'RCP-0014', datetime('now'), 1),
('QR-8ERP7V8NNTI', 'RCP-0015', datetime('now'), 1),
('QR-TPM7MLXHJ20', 'RCP-0016', datetime('now'), 1),
('QR-6XZSNRUMEFQ', 'RCP-0017', datetime('now'), 1),
('QR-CY-HPNFFZSE', 'RCP-0018', datetime('now'), 1),
('QR-V8MFSDXBYJA', 'RCP-0019', datetime('now'), 1),
('QR-5_HBUE9JBQG', 'RCP-0020', datetime('now'), 1),
('QR-LKMMHJDB6EO', 'RCP-0021', datetime('now'), 1),
('QR--1MVZWS4DMO', 'RCP-0022', datetime('now'), 1),
('QR-21RKRH1PJKU', 'RCP-0023', datetime('now'), 1),
('QR-UZ4SI2N6GQG', 'RCP-0024', datetime('now'), 1),
('QR-ROX27GOHEXY', 'RCP-0025', datetime('now'), 1),
('QR-WBF2KV672EU', 'RCP-0026', datetime('now'), 1),
('QR-I3E0IBPVGUO', 'RCP-0027', datetime('now'), 1),
('QR-LN940QJEIWY', 'RCP-0028', datetime('now'), 1),
('QR-9HV-HPHWIKG', 'RCP-0029', datetime('now'), 1),
('QR-LKFIRN4QXNW', 'RCP-0030', datetime('now'), 1);

