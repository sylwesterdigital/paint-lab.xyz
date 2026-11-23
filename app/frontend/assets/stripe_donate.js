/* Paint Lab Stripe Payment Link integration (v0.1.66).
   The buy-button ID and pk_live_ key are publishable identifiers, not secrets.
   Do not load Stripe until the visitor explicitly opens the donation sheet.
   The original PNG download never depends on this module or a payment. */
(()=>{
  'use strict';
  const SCRIPT='https://js.stripe.com/v3/buy-button.js';
  let loader=null;
  function loadStripe(){
    if(loader)return loader;
    loader=new Promise((resolve,reject)=>{
      const script=document.createElement('script');
      script.async=true;script.src=SCRIPT;
      script.onload=resolve;
      script.onerror=()=>reject(new Error('Stripe button unavailable'));
      document.head.appendChild(script);
    });
    return loader;
  }
  function init(){
    for(const trigger of document.querySelectorAll('[data-stripe-dialog-trigger]')){
      trigger.addEventListener('click',()=>{
        const dialog=document.getElementById(trigger.dataset.stripeDialogTrigger);
        if(!dialog)return;
        if(!dialog.open)dialog.showModal();
        const status=dialog.querySelector('[data-stripe-status]');
        if(status)status.textContent='Loading secure Stripe support…';
        // If blocked by a privacy extension or the network, the official
        // payment link stays accessible as a normal anchor inside the sheet.
        loadStripe().then(()=>{
          if(status)status.textContent='Optional support is handled securely by Stripe.';
        },()=>{
          if(status)status.textContent='Stripe button unavailable. Use the secure payment link below.';
        });
      });
    }
    for(const close of document.querySelectorAll('[data-stripe-dialog-close]')){
      close.addEventListener('click',()=>close.closest('dialog')?.close());
    }
    for(const dialog of document.querySelectorAll('dialog[data-stripe-dialog]')){
      dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
      // Prevent painting shortcuts while the donation sheet has keyboard focus.
      dialog.addEventListener('keydown',event=>{if(event.key!=='Escape')event.stopPropagation();});
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
