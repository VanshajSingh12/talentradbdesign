from pathlib import Path
import re

DD = Path("ddl")

# PostgreSQL reserved-word tokens are common in DDL. We only flag them when they are
# used as identifiers (table/column names or FK targets), not when they are SQL keywords
# inside statements/comments. This scan finds all CREATE TABLE/VIEW names plus
# column-name identifiers and checks them against a reserved set.

# Conservative PostgreSQL 16 reserved-word set (identifier-conflicts only).
# These are the tokens that CANNOT be used as bare identifiers.
PG_RESERVED = {
    "all","analyse","analyze","and","any","array","as","asc","asymmetric","at",
    "authorization","backward","begin","between","big","binary","bit","boolean","both",
    "by","cache","called","cardinality","cascade","cascaded","case","cast","catalog",
    "chain","char","character","character varying","check","class","close","cluster",
    "coalesce","collatable","collate","collation","column","columns","concurrent",
    "constraint","constraints","conversion","convert","copy","correlation","cost","create",
    "cross","current","current_catalog","current_date","current_role","current_schema",
    "current_time","current_timestamp","current_user","cursor","cycle","data","database",
    "datetime","day","debian","decimal","declare","default","deferrable","deferred","defined",
    "defwarn","desc","distinct","do","domain","double precision","drop","each","else","end",
    "enum","environment","except","exception","exclusion","execute","exists","explain",
    "extension","external","extract","false","fetch","filter","final","first","float",
    "float4","float8","for","foreign","found","from","full","function","generated","global",
    "granted","greatest","group","grouping","handler","having","header","hold","hour",
    "identity","if","ignore","immediate","in","including","inclusive","increment",
    "index","indices","inheritance","initial","initplan","inner","inout","insensitive",
    "insert","instead","int","int2","int4","int8","integer","intersect","interval","into",
    "invoker","isolation","is","isnull","join","json","jsonb","jsonl","jsonpath","key","kill",
    "label","language","last","lateral","leading","leakproof","left","level","like","limit",
    "list","listen","load","local","locale","location","lock","loose","log","logger","login",
    "long","loop","lower","main","match","materialized","max","maxvalue","message","min",
    "minvalue","minute","mod","mode","modify","month","move","name","names","national",
    "natural","nchar","next","no","none","not","nothing","notify","notnull","now","null",
    "nullif","numeric","object","of","off","offset","oids","on","once","only","opclass",
    "operator","option","or","order","ordered","ordinality","others","otherwise","outer",
    "over","overlaps","overlay","owned","owner","padding","page","parallel",
    "parameter","partitioned","password","percent","persistent","planner","plan","plpgsql",
    "policy","pool","position","power","precision","prepare","prepared","present","primary",
    "print","prior","privileges","procedural","procedure","process","profiler","public",
    "quote","range","rank","read","real","references","reindex","relative","release","rename",
    "repeat","repeatable","replace","replica","reset","resolve","resource","respect","rest",
    "return","returned","returns","revoke","right","role","rollback","row","rows","rule",
    "savepoint","schema","scroll","search","second","security","sequence","serializable",
    "server","session","session_user","set","sets","share","shared","show","shutdown","sign",
    "simulate","smallint","snapshot","some","sql","sqlstate","stability","standart","start",
    "statement","statistics","standby","stddev","stdin","stdout","strict","string","strip",
    "structure","style","subquery","synonym","symmetric","sysdate","system","system_time",
    "system_user","table","tables","tablesample","tablespace","temp","template","temporary",
    "terminate","than","then","tie","time","timestamp","timezone","to","top","trailing",
    "transaction","trigger","true","truncate","trusted","type","types","unbounded","uncommitted",
    "unencrypted","union","unique","unknown","until","update","upgrade","usage","user","using",
    "vacuum","verbose","version","view","volatile","wallet","when","where","while",
    "window","with","without","work","writetext","year","zone","zone_hitrate",
}

def create_names(text):
    # names used in CREATE TABLE / CREATE MATERIALIZED VIEW
    out = set()
    for m in re.finditer(r'(?:CREATE\s+(?:TABLE|MATERIALIZED\s+VIEW)\s+)\S+', text, flags=re.I):
        name = m.group(0).split()[-1].strip('();')
        name = name.split(".")[0].strip('"')
        out.add(name.lower())
    return out

def fk_target_names(text):
    # names referenced in REFERENCES <name>( ... )
    out = set()
    for m in re.finditer(r'REFERENCES\s+(\S+?)\s*\(', text, flags=re.I):
        name = m.group(1).split(".")[0].strip('"').lower()
        out.add(name)
    return out

issue_files = {
    "01_master_data.sql","02_profile.sql","03_jobs_applications.sql",
    "04_administration.sql","05_organisation.sql","06_gig_marketplace.sql",
    "07_licences.sql","08_sourcing.sql","09_subscriptions.sql",
    "10_notifications.sql","11_analytics.sql","12_tier3_stretch.sql",
    "99_documentation.sql",
}

hits = []
for f in sorted(DD.glob("*.sql")):
    if f.name not in issue_files:
        continue
    text = f.read_text(errors="replace")
    names = create_names(text) | fk_target_names(text)
    for n in names:
        if n in PG_RESERVED:
            hits.append((f.name, n))

print("=== RESIDUAL PG-RESERVED IDENTIFIER USAGE ===")
if not hits:
    print("(none)")
else:
    for fname, n in sorted(hits):
        print(f"  {fname:26s} {n}")
