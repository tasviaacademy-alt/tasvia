/* TASVIA Academy: live clock and activity timestamps. */
(function(){
  "use strict";
  if(window.__tasviaTimeFeaturesLoaded)return;
  window.__tasviaTimeFeaturesLoaded=true;
  var zone="Asia/Kolkata",activityNode=null,clockNode=null,patched=false;
  function timeParts(date){
    try{return new Intl.DateTimeFormat("en-IN",{timeZone:zone,hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:true}).format(date||new Date());}
    catch(_){return new Date().toLocaleTimeString();}
  }
  function dateParts(date){
    try{return new Intl.DateTimeFormat("en-IN",{timeZone:zone,weekday:"short",day:"2-digit",month:"short",year:"numeric"}).format(date||new Date());}
    catch(_){return new Date().toLocaleDateString();}
  }
  function setActivity(label,when){
    if(!activityNode)return;
    activityNode.textContent=label+" · "+timeParts(when instanceof Date?when:new Date());
    activityNode.title="Time shown in India Standard Time (Asia/Kolkata)";
  }
  function mountClock(){
    if(clockNode||!document.body)return;
    var header=document.querySelector("header");
    if(!header)return;
    var panel=document.createElement("div");
    panel.id="tasviaTimePanel";
    panel.style.cssText="max-width:1120px;margin:8px auto 0;padding:7px 14px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;border:1px solid rgba(217,174,89,.35);border-radius:11px;background:rgba(255,255,255,.07);color:#F8FAFC;font:600 12px/1.35 system-ui,-apple-system,'Segoe UI',sans-serif";
    var left=document.createElement("div");
    left.style.cssText="display:flex;gap:8px;align-items:center;flex-wrap:wrap";
    var dot=document.createElement("span");
    dot.setAttribute("aria-hidden","true");
    dot.style.cssText="width:7px;height:7px;border-radius:50%;background:#36C98F;box-shadow:0 0 0 3px rgba(54,201,143,.13)";
    var date=document.createElement("span");date.id="tasviaLiveDate";date.style.opacity=".9";
    var time=document.createElement("strong");time.id="tasviaLiveTime";time.style.cssText="color:#E3B75B;font-size:14px;font-variant-numeric:tabular-nums";
    left.append(dot,date,time);
    activityNode=document.createElement("span");
    activityNode.id="tasviaLastActivity";
    activityNode.textContent="Live activity · waiting for update";
    activityNode.style.cssText="opacity:.92;font-size:11px;font-weight:500;max-width:100%;overflow-wrap:anywhere";
    panel.append(left,activityNode);
    header.appendChild(panel);
    clockNode=time;
    function tick(){var now=new Date();date.textContent=dateParts(now);time.textContent=timeParts(now);}
    tick();window.setInterval(tick,1000);
  }
  function category(ref){
    var path=String(ref&&ref.path||"").split("/");
    if(path.length<2)return "";
    var col=path[path.length-2];
    if(col==="attendance")return "attendance";
    if(col==="diary"||col==="homework")return "homework";
    if(col==="parentView")return "parent";
    if(col==="students"||col==="Students")return "student";
    return "";
  }
  function fieldFor(cat){
    if(cat==="attendance")return "attendanceUpdatedAt";
    if(cat==="homework")return "homeworkUpdatedAt";
    if(cat==="parent")return "activityAt";
    if(cat==="student")return "updatedAt";
    return "";
  }
  function stamp(ref,data){
    var cat=category(ref),field=fieldFor(cat);
    if(!cat||!field||!data||typeof data!=="object"||Array.isArray(data))return data;
    var out=Object.assign({},data);
    try{
      var fv=window.firebase&&firebase.firestore&&firebase.firestore.FieldValue;
      if(fv&&typeof fv.serverTimestamp==="function")out[field]=fv.serverTimestamp();
      if(cat==="parent")out.activityAtClient=Date.now();
    }catch(_){}
    return out;
  }
  function activityLabel(cat){
    if(cat==="attendance")return "Attendance saved";
    if(cat==="homework")return "Homework saved";
    if(cat==="parent")return "Parent portal synced";
    if(cat==="student")return "Student record saved";
    return "";
  }
  function afterWrite(promise,cat){
    return Promise.resolve(promise).then(function(value){
      var label=activityLabel(cat);if(label)setActivity(label,new Date());
      return value;
    });
  }
  function patchFirestore(){
    if(patched||!window.firebase||!firebase.firestore)return false;
    var fs=firebase.firestore;
    try{
      var dp=fs.DocumentReference&&fs.DocumentReference.prototype;
      if(dp){
        if(typeof dp.set==="function"&&!dp.set.__tasviaWrapped){
          var originalSet=dp.set;
          var wrappedSet=function(data,options){var cat=category(this);return afterWrite(originalSet.call(this,stamp(this,data),options),cat);};
          wrappedSet.__tasviaWrapped=true;dp.set=wrappedSet;
        }
        if(typeof dp.update==="function"&&!dp.update.__tasviaWrapped){
          var originalUpdate=dp.update;
          var wrappedUpdate=function(){
            var args=Array.prototype.slice.call(arguments),cat=category(this),field=fieldFor(cat);
            if(field){
              if(args[0]&&typeof args[0]==="object"&&!Array.isArray(args[0]))args[0]=stamp(this,args[0]);
              else args.push(field,(firebase.firestore.FieldValue&&firebase.firestore.FieldValue.serverTimestamp?firebase.firestore.FieldValue.serverTimestamp():Date.now()));
            }
            return afterWrite(originalUpdate.apply(this,args),cat);
          };
          wrappedUpdate.__tasviaWrapped=true;dp.update=wrappedUpdate;
        }
      }
      var cp=fs.CollectionReference&&fs.CollectionReference.prototype;
      if(cp&&typeof cp.add==="function"&&!cp.add.__tasviaWrapped){
        var originalAdd=cp.add;
        var wrappedAdd=function(data){var cat=category({path:this.path+"/_new"});return afterWrite(originalAdd.call(this,stamp({path:this.path+"/_new"},data)),cat);};
        wrappedAdd.__tasviaWrapped=true;cp.add=wrappedAdd;
      }
      var bp=fs.WriteBatch&&fs.WriteBatch.prototype;
      if(bp){
        ["set","update"].forEach(function(method){
          if(typeof bp[method]!=="function"||bp[method].__tasviaWrapped)return;
          var original=bp[method];
          var wrapped=function(ref,data,options){
            var cat=category(ref),field=fieldFor(cat),args=Array.prototype.slice.call(arguments);
            if(method==="set")args[1]=stamp(ref,data);
            else if(field){
              if(data&&typeof data==="object"&&!Array.isArray(data))args[1]=stamp(ref,data);
              else args.push(field,(firebase.firestore.FieldValue&&firebase.firestore.FieldValue.serverTimestamp?firebase.firestore.FieldValue.serverTimestamp():Date.now()));
            }
            if(cat){this.__tasviaActivityCats=this.__tasviaActivityCats||[];if(this.__tasviaActivityCats.indexOf(cat)<0)this.__tasviaActivityCats.push(cat);}
            return original.apply(this,args);
          };
          wrapped.__tasviaWrapped=true;bp[method]=wrapped;
        });
        if(typeof bp.commit==="function"&&!bp.commit.__tasviaWrapped){
          var originalCommit=bp.commit;
          var wrappedCommit=function(){var self=this,cats=(self.__tasviaActivityCats||[]).slice();return Promise.resolve(originalCommit.apply(self,arguments)).then(function(v){cats.forEach(function(c){setActivity(activityLabel(c),new Date())});return v;});};
          wrappedCommit.__tasviaWrapped=true;bp.commit=wrappedCommit;
        }
      }
      var tp=fs.Transaction&&fs.Transaction.prototype;
      if(tp){
        ["set","update"].forEach(function(method){
          if(typeof tp[method]!=="function"||tp[method].__tasviaWrapped)return;
          var original=tp[method];
          var wrapped=function(ref,data,options){var cat=category(ref),field=fieldFor(cat),args=Array.prototype.slice.call(arguments);if(method==="set")args[1]=stamp(ref,data);else if(field){if(data&&typeof data==="object"&&!Array.isArray(data))args[1]=stamp(ref,data);else args.push(field,(firebase.firestore.FieldValue&&firebase.firestore.FieldValue.serverTimestamp?firebase.firestore.FieldValue.serverTimestamp():Date.now()));}if(cat)setActivity(activityLabel(cat),new Date());return original.apply(this,args);};
          wrapped.__tasviaWrapped=true;tp[method]=wrapped;
        });
      }
      patched=true;
      return true;
    }catch(e){console.warn("TASVIA timestamp tracking could not attach:",e);return false;}
  }
  function wrapParentRender(){
    var fn=window.__tasviaParentLiveRender;
    if(typeof fn!=="function"||fn.__tasviaTimestampWrapped)return;
    var wrapped=function(data,code){
      var result=fn.apply(this,arguments);
      var when=Date.now();
      try{
        var raw=data&&data.activityAtClient;
        if(raw&&Number.isFinite(Number(raw)))when=Number(raw);
        else if(data&&data.activityAt&&typeof data.activityAt.toDate==="function")when=data.activityAt.toDate().getTime();
      }catch(_){}
      setActivity("Parent portal synced",new Date(when));
      return result;
    };
    wrapped.__tasviaTimestampWrapped=true;
    window.__tasviaParentLiveRender=wrapped;
  }
  function start(){
    mountClock();
    patchFirestore();
    wrapParentRender();
    if(!patched||typeof window.__tasviaParentLiveRender!=="function")window.setInterval(function(){patchFirestore();wrapParentRender();},1000);
    var mo=new MutationObserver(function(){
      var live=document.getElementById("tasviaLiveSyncStatus");
      if(live&&/LIVE|connected/i.test(live.textContent||""))setActivity("Parent portal synced",new Date());
    });
    mo.observe(document.body,{childList:true,subtree:true,characterData:true});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});else start();
})();