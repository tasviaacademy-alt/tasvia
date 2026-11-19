/* TASVIA Academy — Staff Leave Applications
   Staff can submit and view their own requests. Admin can review all requests.
   Data is stored in Firestore collection: leaveApplications.
*/
(function(){
  if (window.__tasviaLeaveModuleLoaded) return;
  window.__tasviaLeaveModuleLoaded = true;
  if (!S.leaveApplications) S.leaveApplications = {};
  let subscribedKey = "";

  function leaveEmail(){
    return String(window.currentUser && window.currentUser.email || "").trim().toLowerCase();
  }
  function leaveRows(){
    return Object.entries(S.leaveApplications || {})
      .map(([id,row])=>Object.assign({id},row||{}))
      .sort((a,b)=>(Number(b.createdAt)||0)-(Number(a.createdAt)||0));
  }
  function leaveDays(start,end){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(start)||!/^\d{4}-\d{2}-\d{2}$/.test(end))return 0;
    const a=Date.parse(start+"T00:00:00Z"),b=Date.parse(end+"T00:00:00Z");
    return Number.isFinite(a)&&Number.isFinite(b)&&b>=a?Math.floor((b-a)/86400000)+1:0;
  }
  function leaveTag(status){
    if(status==="Approved")return '<span class="tag ok">Approved</span>';
    if(status==="Rejected")return '<span class="tag due">Rejected</span>';
    return '<span class="tag n">Pending</span>';
  }
  function ensureLeaveData(){
    if(!db)return;
    const email=leaveEmail(),admin=isAdmin(),key=admin?"admin":email;
    if(!email||subscribedKey===key)return;
    subscribedKey=key;
    const query=admin
      ? db.collection("leaveApplications").limit(300)
      : db.collection("leaveApplications").where("applicantEmail","==",email).limit(100);
    const unsub=query.onSnapshot(snap=>{
      const rows={};
      snap.docs.forEach(doc=>rows[doc.id]=doc.data()||{});
      S.leaveApplications=rows;
      scheduleRender();
    },err=>{
      console.error("TASVIA leave applications:",err);
      subscribedKey="";
      toast(err&&err.code==="permission-denied"
        ?"You do not have permission to view these leave applications."
        :"Unable to load leave applications. Check your connection.");
    });
    if(Array.isArray(unsubs))unsubs.push(unsub);
  }
  function renderLeaveView(){
    ensureLeaveData();
    const admin=isAdmin(),rows=leaveRows();
    const pending=rows.filter(x=>x.status==="Pending").length;
    const approved=rows.filter(x=>x.status==="Approved").length;
    const rejected=rows.filter(x=>x.status==="Rejected").length;
    let h=mhead("Leave applications",admin?"Review staff leave requests":"Apply for leave and track your requests",
      '<button class="btn gold" data-act="leaveApply">Apply for leave</button>');
    if(admin){
      h+='<div class="board"><div><b>'+rows.length+'</b><small>Total requests</small></div><div class="pp"><b>'+pending+'</b><small>Pending</small></div><div class="aa"><b>'+approved+'</b><small>Approved</small></div></div>';
    }else{
      h+='<div class="board"><div><b>'+rows.length+'</b><small>My requests</small></div><div class="pp"><b>'+pending+'</b><small>Pending</small></div><div class="aa"><b>'+approved+'</b><small>Approved</small></div></div>';
    }
    if(!rows.length){
      h+='<div class="empty"><p>'+(admin?"No leave applications have been submitted yet.":"You have not applied for leave yet.")+'</p><button class="btn gold" data-act="leaveApply">Apply for leave</button></div>';
      return h;
    }
    h+='<div class="list">'+rows.map(x=>{
      const range=(x.startDate?nice(x.startDate):"–")+(x.endDate&&x.endDate!==x.startDate?" – "+nice(x.endDate):"");
      return '<button class="item" data-act="leaveOpen" data-id="'+esc(x.id)+'"><div class="grow"><div class="nm">'+esc(x.applicantName||x.applicantEmail||"Staff")+(admin?' · '+esc(x.leaveType||"Leave"):"")+'</div><div class="mt">'+(admin?esc(x.applicantEmail||"")+" · ":"")+esc(range)+' · '+(Number(x.days)||0)+' day(s)</div></div>'+leaveTag(x.status||"Pending")+'</button>';
    }).join("")+'</div>';
    return h;
  }
  function leaveForm(){
    const email=leaveEmail();
    if(!window.currentUser||!email){toast("Please sign in with your TASVIA staff account.");return;}
    const who=String(window.currentUser.name||email);
    openSheet("Apply for leave",'<form id="fLeaveApply">'+
      '<label class="f">Leave type<select name="leaveType" required><option value="Casual">Casual leave</option><option value="Sick">Sick leave</option><option value="Emergency">Emergency leave</option><option value="Personal">Personal leave</option><option value="Other">Other</option></select></label>'+
      '<div class="two"><label class="f">From date<input name="startDate" type="date" min="'+today()+'" value="'+today()+'" required></label><label class="f">To date<input name="endDate" type="date" min="'+today()+'" value="'+today()+'" required></label></div>'+
      '<div class="notice" id="leaveDayCount">Duration: 1 day</div>'+
      '<label class="f">Reason<textarea name="reason" rows="4" maxlength="1000" minlength="5" required placeholder="Briefly explain the reason for your leave"></textarea></label>'+
      '<p class="sub">Applying as: '+esc(who)+'</p>'+
      '<div class="acts"><button class="btn gold" type="submit">Submit application</button></div></form>');
  }
  function leaveSheet(id){
    const x=(S.leaveApplications||{})[id];
    if(!x)return;
    const admin=isAdmin(),mine=String(x.applicantEmail||"").toLowerCase()===leaveEmail();
    if(!admin&&!mine){toast("You can only view your own leave applications.");return;}
    const range=(x.startDate?nice(x.startDate):"–")+(x.endDate&&x.endDate!==x.startDate?" – "+nice(x.endDate):"");
    let body='<div class="card"><dl class="kv">'+
      '<dt>Staff member</dt><dd>'+esc(x.applicantName||"–")+'</dd>'+
      '<dt>Email</dt><dd>'+esc(x.applicantEmail||"–")+'</dd>'+
      '<dt>Leave type</dt><dd>'+esc(x.leaveType||"–")+'</dd>'+
      '<dt>Dates</dt><dd>'+esc(range)+'</dd>'+
      '<dt>Duration</dt><dd>'+Number(x.days||0)+' day(s)</dd>'+
      '<dt>Status</dt><dd>'+leaveTag(x.status||"Pending")+'</dd>'+
      '<dt>Applied on</dt><dd>'+(x.createdAt?new Date(x.createdAt).toLocaleString("en-IN"):"–")+'</dd>'+
      '</dl><p style="white-space:pre-wrap;margin:12px 0 0"><b>Reason:</b><br>'+esc(x.reason||"–")+'</p>'+
      (x.reviewNote?'<p style="white-space:pre-wrap;margin:10px 0 0"><b>Admin note:</b><br>'+esc(x.reviewNote)+'</p>':"")+
      (x.reviewedByName?'<p class="sub">Reviewed by '+esc(x.reviewedByName)+'</p>':"")+
      '</div>';
    if(admin&&(x.status||"Pending")==="Pending"){
      body+='<form id="fLeaveReview" data-id="'+esc(id)+'">'+
        '<label class="f">Decision<select name="status" required><option value="Approved">Approve leave</option><option value="Rejected">Reject leave</option></select></label>'+
        '<label class="f">Admin note (optional)<textarea name="reviewNote" rows="3" maxlength="500" placeholder="Add a note for the staff member"></textarea></label>'+
        '<div class="acts"><button class="btn gold" type="submit">Save decision</button></div></form>';
    }
    openSheet("Leave request",body);
  }

  window.tasviaLeaveView=renderLeaveView;

  document.addEventListener("click",function(e){
    const b=e.target.closest("[data-act]");
    if(!b)return;
    const act=b.dataset.act;
    if(act==="more"&&b.dataset.k==="leave"){
      e.preventDefault();e.stopImmediatePropagation();
      UI.more="leave";UI.tab="more";UI.dashboardHome=false;
      ensureLeaveData();render();window.scrollTo(0,0);return;
    }
    if(act==="leaveApply"){
      e.preventDefault();e.stopImmediatePropagation();leaveForm();return;
    }
    if(act==="leaveOpen"){
      e.preventDefault();e.stopImmediatePropagation();leaveSheet(b.dataset.id);return;
    }
  },true);

  document.addEventListener("input",function(e){
    if(!e.target||!["fLeaveApply"].includes(e.target.form&&e.target.form.id))return;
    if(e.target.name!=="startDate"&&e.target.name!=="endDate")return;
    const form=e.target.form,fd=new FormData(form),days=leaveDays(String(fd.get("startDate")||""),String(fd.get("endDate")||""));
    const hint=form.querySelector("#leaveDayCount");
    if(hint)hint.textContent=days?"Duration: "+days+" day(s)":"Please choose a valid date range.";
  });

  document.addEventListener("submit",async function(e){
    const f=e.target;
    if(!f||!(f.id==="fLeaveApply"||f.id==="fLeaveReview"))return;
    e.preventDefault();e.stopImmediatePropagation();
    if(f.dataset.saving==="1")return;
    f.dataset.saving="1";
    const button=f.querySelector('button[type="submit"]');
    if(button){button.disabled=true;button.textContent="Saving…";}
    const d=Object.fromEntries(new FormData(f));
    try{
      if(f.id==="fLeaveApply"){
        const email=leaveEmail(),start=String(d.startDate||""),end=String(d.endDate||"");
        const days=leaveDays(start,end),reason=String(d.reason||"").trim();
        if(!window.currentUser||!email)throw new Error("Please sign in with your TASVIA staff account.");
        if(!days)throw new Error("Please select a valid start and end date.");
        if(start<today())throw new Error("Leave applications must start today or later.");
        if(reason.length<5)throw new Error("Please enter a reason (at least 5 characters).");
        if(!["Casual","Sick","Emergency","Personal","Other"].includes(d.leaveType))throw new Error("Select a valid leave type.");
        if(!db)throw new Error("Database is not connected. Please reload and try again.");
        const id=uid("leave"),now=Date.now();
        const row={applicantEmail:email,applicantName:String(window.currentUser.name||email),leaveType:d.leaveType,startDate:start,endDate:end,days,reason,status:"Pending",createdAt:now,updatedAt:now};
        await db.collection("leaveApplications").doc(id).set(row);
        S.leaveApplications=S.leaveApplications||{};S.leaveApplications[id]=row;
        closeSheet();render();toast("Leave application submitted successfully.");
      }else{
        if(!requireAdmin())throw new Error("Admin access required.");
        const id=f.dataset.id,x=(S.leaveApplications||{})[id];
        if(!x||x.status!=="Pending")throw new Error("This request has already been reviewed.");
        const status=d.status;
        if(!["Approved","Rejected"].includes(status))throw new Error("Choose Approve or Reject.");
        const patch={status,reviewNote:String(d.reviewNote||"").trim(),reviewedAt:Date.now(),reviewedByEmail:leaveEmail(),reviewedByName:String(window.currentUser.name||"TASVIA Admin"),updatedAt:Date.now()};
        await db.collection("leaveApplications").doc(id).update(patch);
        S.leaveApplications[id]=Object.assign({},x,patch);
        closeSheet();render();toast("Leave request "+status.toLowerCase()+".");
      }
    }catch(err){
      console.error("TASVIA leave save:",err);
      toast(err&&err.message?err.message:"Unable to save the leave request.");
      f.dataset.saving="0";
      if(button){button.disabled=false;button.textContent=f.id==="fLeaveApply"?"Submit application":"Save decision";}
    }
  },true);
})();