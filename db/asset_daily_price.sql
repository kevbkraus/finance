CREATE TABLE "asset_daily_price" (
	"ticker"	INTEGER,
	"date"	TEXT,
	"adj_close"	NUMERIC,
	PRIMARY KEY("ticker","date")
)