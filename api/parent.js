// TASVIA Academy parent portal API proxy
// Reads only the public parentView document already exposed by Firestore rules.
export default async function handler(req,res){
  res.setHeader("Access-Control-Allow-Origin","https://apk.tasviaacademy.com");
  res.setHeader("Access-Control-Allow-Methods","GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers","Content-Type");
  res.setHeader("Cache-Control","no-store, max-age=0");
  if(req.method==="OPTIONS")return res.status(204).end();
  try{
    const code=String(req.query?.code||"").trim().toUpperCase();
    if(!/^[A-Z0-9][A-Z0-9._-]{2,63}$/.test(code)){
      return res.status(400).json({error:"Invalid Student ID"});
    }
    const url="https://firestore.googleapis.com/v1/projects/tasvia-academy/databases/(default)/documents/parentView/"+encodeURIComponent(code);
    const r=await fetch(url,{cache:"no-store"});
    if(r.status===404)return res.status(404).json({error:"Student not found"});
    const body=await r.text();
    res.status(r.status).setHeader("Content-Type","application/json");
    return res.send(body);
  }catch(e){
    console.error("Parent API error",e);
    return res.status(502).json({error:"Parent data service unavailable"});
  }
}
