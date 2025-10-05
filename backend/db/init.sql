-- JAN-URL マッピングテーブル
CREATE TABLE jan_url_mapping (
    id SERIAL PRIMARY KEY,
    jan_code VARCHAR(13) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    brand VARCHAR(100),
    product_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_jan_code ON jan_url_mapping(jan_code);

-- サンプルデータ投入（架空の商品）
INSERT INTO jan_url_mapping (jan_code, url, brand, product_name) VALUES
    ('4900000000001', 'https://example.com/products/outdoor-jacket-001', 'Mountain Gear', 'Alpine Pro Jacket'),
    ('4900000000002', 'https://example.com/products/running-shoes-002', 'RunFast', 'Speed Runner X1');

-- 更新日時を自動更新するトリガー関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- トリガー設定
CREATE TRIGGER update_jan_url_mapping_updated_at BEFORE UPDATE ON jan_url_mapping
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
