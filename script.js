let homes=[];
const grid=document.getElementById("homesGrid");
const note=document.getElementById("searchNote");
const cityNames={brussels:"Brussels",antwerp:"Antwerp",ghent:"Ghent",bruges:"Bruges",leuven:"Leuven",liege:"Liège",mechelen:"Mechelen",namur:"Namur",waterloo:"Waterloo",knokke:"Knokke"};

async function loadHomes(){
  try{
    const response=await fetch("/data/listings.json",{cache:"no-store"});
    if(!response.ok) throw new Error("Listing data unavailable");
    const data=await response.json();
    homes=(data.listings||[]).filter(h=>h && h.isIllustrative !== false).slice(0,3);
  }catch(error){
    homes=[];
    console.warn("Homes in Belgium homepage listing data could not be loaded.",error);
  }
}


function render(items){
  if(!items.length){
    grid.innerHTML='<div class="empty-state"><strong>No example homes match those filters yet.</strong><p>We are preparing more inventory. Try another city or property type.</p><button type="button" id="resetSearch" class="reset-button">Show all examples</button></div>';
    document.getElementById("resetSearch").addEventListener("click",()=>{document.getElementById("type").value="all";document.getElementById("city").value="all";loadHomes().then(()=>render(homes));note.textContent="Showing selected examples. New inventory can be added as listings become available.";});
    return;
  }
  grid.innerHTML=items.map(h=>'<article class="property"><a class="property-link" href="'+h.url+'"><div class="property-image" style="background-image:url("'+h.image+'")"><span class="badge">'+(h.type==="house"?"HOUSE":"APARTMENT")+'</span></div></a><div class="property-copy"><span class="sample-label">ILLUSTRATIVE EXAMPLE</span><h3>'+h.title+'</h3><p>'+cityNames[h.city]+' · '+h.meta+'</p><div class="price">'+h.price+'</div></div></article>').join("");
}

render(homes);

document.getElementById("searchForm").addEventListener("submit",function(e){
  e.preventDefault();
  const type=document.getElementById("type").value;
  const city=document.getElementById("city").value;
  const params=new URLSearchParams();
  if(type!=="all") params.set("type",type);
  if(city!=="all") params.set("city",city);
  window.location.href="/homes.html"+(params.toString()?"?"+params.toString():"");
});

/* Lightweight interaction layer for the homepage */
const heroArt=document.querySelector(".hero-art");
if(heroArt && !window.matchMedia("(prefers-reduced-motion: reduce)").matches){
  let raf=0;
  document.addEventListener("pointermove",e=>{
    if(raf) return;
    raf=requestAnimationFrame(()=>{
      const r=heroArt.getBoundingClientRect();
      if(r.top<window.innerHeight && r.bottom>0){
        const x=(e.clientX-r.left)/r.width-.5;
        const y=(e.clientY-r.top)/r.height-.5;
        heroArt.style.transform="perspective(900px) rotateY("+x*2.2+"deg) rotateX("+(-y*1.8)+"deg)";
      }
      raf=0;
    });
  });
  heroArt.addEventListener("pointerleave",()=>{heroArt.style.transform=""});
}
