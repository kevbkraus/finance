CREATE TABLE "asset_daily_price" (
	"ticker"	INTEGER,
	"date"	TEXT,
	"close"	NUMERIC,
	PRIMARY KEY("ticker","date")
)