CREATE TABLE IF NOT EXISTS node_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    NodeID VARCHAR(12) NOT NULL,
    payload VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)