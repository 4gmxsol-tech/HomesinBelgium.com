const homes=[
{title:"Refined city apartment",city:"brussels",type:"apartment",price:"€425,000",meta:"2 beds · 1 bath",image:"https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1100&q=80",url:"/properties/brussels-refined-city-apartment.html"},
{title:"Light-filled Antwerp townhouse",city:"antwerp",type:"house",price:"€589,000",meta:"3 beds · 2 baths",image:"https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=1100&q=80",url:"/properties/antwerp-townhouse.html"},
{title:"Character home near Ghent",city:"ghent",type:"house",price:"€472,000",meta:"3 beds · 2 baths",image:"https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=1100&q=80",url:"/properties/ghent-character-home.html"}
];

const grid=document.getElementById("homesGrid");
const note=document.getElementById("searchNote");
const cityNames={brussels:"Brussels",antwerp:"Antwerp",ghent:"Ghent",bruges:"Bruges",leuven:"Leuven",liege:"Liège",mechelen:"Mechelen",namur:"Namur",waterloo:"Waterloo",knokke:"Knokke"};

function render(items){
  if(!items.length){
    grid.innerHTML='<div class="empty-state"><strong>No example homes match those filters yet.</strong><p>We are preparing more inventory. Try another city or property type.</p><button type="button" id="resetSearch" class="reset-button">Show all examples</button></div>';
    document.getElementById("resetSearch").addEventListener("click",()=>{document.getElementById("type").value="all";document.getElementById("city").value="all";render(homes);note.textContent="Showing selected examples. New inventory can be added as listings become available.";});
    return;
  }
  grid.innerHTML=items.map(h=>'<article class="property"><a class="property-link" href="'+h.url+'"><div class="property-image" style="background-image:url("'+h.image+'")"><span class="badge">'+(h.type==="house"?"HOUSE":"APARTMENT")+'</span></div></a><div class="property-copy"><span class="sample-label">ILLUSTRATIVE EXAMPLE</span><h3>'+h.title+'</h3><p>'+cityNames[h.city]+' · '+h.meta+'</p><div class="price">'+h.price+'</div></div></article>').join("");
}

render(homes);

document.getElementById("searchForm").addEventListener("submit",function(e){
  e.preventDefault();
  const type=document.getElementById("type").value;
  const city=document.getElementById("city").value;
  const filtered=homes.filter(h=>(type==="all"||h.type===type)&&(city==="all"||h.city===city));
  render(filtered);
  note.textContent=filtered.length
    ? "Showing "+filtered.length+" illustrative example"+(filtered.length===1?"":"s")+" matching your search."
    : "No illustrative examples match this search yet.";
  document.getElementById("homes").scrollIntoView({behavior:"smooth"});
});