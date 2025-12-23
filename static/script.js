// Fetch expenses and populate table (existing behavior)
function loadExpenses(){
	fetch('/get-expenses', buildAuthOptions())
	.then(res => res.json())
	.then(data => {
		const body = document.getElementById('expenseBody');
		if(!body) return;
		body.innerHTML = '';
		if(!data || data.length === 0){
			body.innerHTML = '<tr><td colspan="5" class="empty">No expenses yet.</td></tr>';
			return;
		}

		// Normalize and sort by date descending
		data.sort((a,b)=> {
			const da = a.date || '';
			const db = b.date || '';
			return db.localeCompare(da);
		});

		// Group by YYYY-MM
		const groups = {};
		for(const exp of data){
			let month = 'Unknown';
			if(exp.date && typeof exp.date === 'string' && exp.date.length >= 7) month = exp.date.slice(0,7);
			if(!groups[month]) groups[month] = [];
			groups[month].push(exp);
		}

		function formatMonth(yyyymm){
			if(!yyyymm || yyyymm === 'Unknown') return 'Unknown';
			const [y, m] = yyyymm.split('-');
			try{
				const d = new Date(parseInt(y,10), parseInt(m,10)-1, 1);
				return d.toLocaleString('en-US', { month: 'long', year: 'numeric' });
			}catch(e){ return yyyymm; }
		}

		// Render months (descending)
		const months = Object.keys(groups).sort((a,b)=> b.localeCompare(a));
		months.forEach((m, idx) => {
			// header row (clickable)
			const hdr = document.createElement('tr');
			hdr.className = 'month-row month-header-row';
			hdr.style.cursor = 'pointer';
			hdr.innerHTML = `<td colspan="5" class="month-header">${formatMonth(m)}</td>`;
			body.appendChild(hdr);

			// content wrapper row
			const contentTr = document.createElement('tr');
			contentTr.className = 'month-content-row';
			const contentTd = document.createElement('td');
			contentTd.colSpan = 5;

			const wrapper = document.createElement('div');
			wrapper.className = 'month-contents';
			// start closed; slide by animating max-height
			wrapper.style.overflow = 'hidden';
			wrapper.style.maxHeight = '0px';
			wrapper.style.transition = 'max-height 240ms ease';

			// create inner table so visual columns/rows match original exactly
			const innerTable = document.createElement('table');
			innerTable.style.width = '100%';
			innerTable.style.borderCollapse = 'collapse';
			const innerTbody = document.createElement('tbody');

			// sort entries in this month by date desc
			groups[m].sort((a,b)=> (b.date || '').localeCompare(a.date || ''));

			for(const exp of groups[m]){
				const row = document.createElement('tr');
				// keep fields exactly as original: amount, category, note, date (then actions td)
				row.innerHTML = `<td>${exp.amount}</td><td>${exp.category}</td><td>${exp.note || ''}</td><td>${exp.date}</td>`;
				const actions = document.createElement('td');
				actions.style.whiteSpace = 'nowrap';
				const editBtn = document.createElement('button');
				editBtn.className = 'btn ghost action-btn';
				editBtn.textContent = 'Edit';
				editBtn.onclick = ()=> editExpense(exp.id);
				const delBtn = document.createElement('button');
				delBtn.className = 'btn secondary action-btn';
				delBtn.textContent = 'Delete';
				delBtn.onclick = ()=> deleteExpense(exp.id);
				actions.appendChild(editBtn);
				actions.appendChild(delBtn);
				row.appendChild(actions);
				innerTbody.appendChild(row);
			}

			innerTable.appendChild(innerTbody);
			wrapper.appendChild(innerTable);
			contentTd.appendChild(wrapper);
			contentTr.appendChild(contentTd);
			body.appendChild(contentTr);

			// toggle behavior: click header to expand/collapse
			hdr.addEventListener('click', ()=>{
				const isClosed = wrapper.style.maxHeight === '0px' || wrapper.style.maxHeight === '';
				if(isClosed){
					wrapper.style.maxHeight = wrapper.scrollHeight + 'px';
					hdr.classList.add('open');
				} else {
					wrapper.style.maxHeight = '0px';
					hdr.classList.remove('open');
				}
			});

			// default: open most recent month (first in list)
			if(idx === 0){
				requestAnimationFrame(()=>{ wrapper.style.maxHeight = wrapper.scrollHeight + 'px'; hdr.classList.add('open'); });
			}
		});
	}).catch(err => console.error(err));
}

// Helper to build fetch options that include Authorization header when token exists,
// otherwise fall back to same-origin credentials so session cookies work.
function buildAuthOptions(method='GET', data=null){
	const token = (()=>{ try{ return localStorage.getItem('token'); }catch(e){ return null; } })();
	const opts = { method: method };
	const headers = {};
	if(token){ headers['Authorization'] = 'Bearer ' + token; }
	else { opts.credentials = 'same-origin'; }
	if(data !== null){ headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(data); }
	if(Object.keys(headers).length) opts.headers = headers;
	return opts;
}

function deleteExpense(id){
	if(!confirm('Delete this expense?')) return;
	fetch('/api/expense/'+id, buildAuthOptions('DELETE'))
	.then(r=>{ if(r.ok){ loadExpenses(); loadSummary(); } else r.json().then(j=>alert(j.error||'Delete failed')) })
	.catch(e=>alert('Network error'));
}

function editExpense(id){
	// simple prompt-based edit for now
	const newAmount = prompt('New amount (leave blank to keep):');
	const newCategory = prompt('New category (leave blank to keep):');
	const newNote = prompt('New note (leave blank to keep):');
	const payload = {};
	if(newAmount) payload.amount = parseFloat(newAmount);
	if(newCategory) payload.category = newCategory;
	if(newNote) payload.note = newNote;
	if(Object.keys(payload).length===0) return;
	fetch('/api/expense/'+id, buildAuthOptions('PUT', payload))
	.then(r=>{ if(r.ok){ loadExpenses(); loadSummary(); } else r.json().then(j=>alert(j.error||'Update failed')) })
	.catch(e=>alert('Network error'));
}

// Budget functions
function loadBudget(){
	return fetch('/api/budget', buildAuthOptions())
	.then(r => {
		if(r.status === 401) throw new Error('not-auth');
		return r.json();
	})
	.then(j=>{
		const el = document.getElementById('budgetAmount');
		if(el) el.value = (j.amount || '') ;
		const msg = document.getElementById('budgetMsg');
		if(msg) msg.textContent = `Month: ${j.month}`;
		// store current budget for comparison
		window._currentBudget = parseFloat(j.amount) || 0;
		window._currentBudgetMonth = j.month;
		return j;
	}).catch(e=>{
		if(e.message === 'not-auth') window.location = '/login';
		else console.error(e);
	});
}

function setBudget(){
	const v = parseFloat(document.getElementById('budgetAmount').value || 0);
	fetch('/api/budget', buildAuthOptions('POST', {amount: v}))
	.then(r => {
		if(r.status === 401) throw new Error('not-auth');
		if(!r.ok) return r.json().then(j=>{ throw new Error(j.error || 'failed') });
		return r.json();
	})
	.then(j=>{
		const msg = document.getElementById('budgetMsg');
		if(msg) msg.textContent = `Set ${j.month} → ${j.amount.toFixed(2)}`;
		// refresh summary and expenses
		loadSummary();
		loadBudget();
	})
	.catch(e=>{
		if(e.message === 'not-auth') window.location = '/login';
		else {
			const msg = document.getElementById('budgetMsg');
			if(msg) msg.textContent = 'Unable to set budget: ' + e.message;
		}
	});
}

// Fetch summary and render charts using Chart.js
function loadSummary(){
	fetch('/api/summary', buildAuthOptions())
	.then(res => {
		if(res.status === 401) throw new Error('not-auth');
		return res.json();
	})
	.then(data => {
		document.getElementById('totalAmount').textContent = data.total.toFixed(2);

		// category chart (page-specific or dashboard)
		const catLabels = data.by_category.map(c => c.category);
		const catData = data.by_category.map(c => c.total);
		if(document.getElementById('categoryChart')){
			const catCtx = document.getElementById('categoryChart').getContext('2d');
			if(window._catChart) window._catChart.destroy();
			window._catChart = new Chart(catCtx, {
				type: 'doughnut',
				data: { labels: catLabels, datasets: [{ data: catData, backgroundColor: generateColors(catData.length) }] },
				options: { plugins: { legend: { position: 'bottom' } } }
			});
		}

		if(document.getElementById('dashCategoryChart')){
			const catCtx2 = document.getElementById('dashCategoryChart').getContext('2d');
			if(window._dashCatChart) window._dashCatChart.destroy();
			window._dashCatChart = new Chart(catCtx2, {
				type: 'doughnut',
				data: { labels: catLabels, datasets: [{ data: catData, backgroundColor: generateColors(catData.length) }] },
				options: { plugins: { legend: { position: 'bottom' } } }
			});
		}

		// monthly chart
		const monthLabels = data.monthly.map(m => m.month);
		const monthData = data.monthly.map(m => m.total);
		if(document.getElementById('monthlyChart')){
			const monthCtx = document.getElementById('monthlyChart').getContext('2d');
			if(window._monthChart) window._monthChart.destroy();
			window._monthChart = new Chart(monthCtx, {
				type: 'bar',
				data: { labels: monthLabels, datasets: [{ label: 'Spent', data: monthData, backgroundColor: 'rgba(79,70,229,0.8)' }] },
				options: { scales: { y: { beginAtZero:true } }, plugins: { legend: { display:false } } }
			});
		}

		if(document.getElementById('dashMonthlyChart')){
			const monthCtx2 = document.getElementById('dashMonthlyChart').getContext('2d');
			if(window._dashMonthChart) window._dashMonthChart.destroy();
			window._dashMonthChart = new Chart(monthCtx2, {
				type: 'bar',
				data: { labels: monthLabels, datasets: [{ label: 'Spent', data: monthData, backgroundColor: 'rgba(79,70,229,0.8)' }] },
				options: { scales: { y: { beginAtZero:true } }, plugins: { legend: { display:false } } }
			});
		}

		// check budget exceed and update progress/alert
		try{
			const budget = parseFloat(window._currentBudget || 0);
			const total = parseFloat(data.total || 0);
			const alertEl = document.getElementById('budgetAlert');
			const progInner = document.getElementById('budgetProgressInner');
			if(progInner){
				if(budget > 0){
					let pct = Math.round((total / budget) * 100);
					if(pct < 0) pct = 0;
					if(pct > 100) pct = 100;
					progInner.style.width = pct + '%';
				} else {
					progInner.style.width = '0%';
				}
			}

			if(alertEl){
				if(budget > 0 && total > budget){
					alertEl.style.display = 'block';
					alertEl.className = 'budget-alert warn';
					const over = (total - budget).toFixed(2);
					alertEl.textContent = `Budget exceeded by ${over} (${((total/budget)*100).toFixed(0)}%)`;
				} else if(budget > 0){
					alertEl.style.display = 'block';
					alertEl.className = 'budget-alert ok';
					const pct = ((total / budget) * 100).toFixed(0);
					alertEl.textContent = `${pct}% of budget used`;
				} else {
					alertEl.style.display = 'none';
				}
			}
		}catch(e){ console.error(e) }
	}).catch(err => {
		if(err.message === 'not-auth'){
			// redirect to login
			window.location = '/login';
		} else console.error(err);
	});
}

function generateColors(n){
	const palette = ['#4f46e5','#06b6d4','#f59e0b','#10b981','#ef4444','#8b5cf6','#ec4899','#06b6d4','#f97316','#ecd1de42'];
	const out = [];
	for(let i=0;i<n;i++) out.push(palette[i % palette.length]);
	return out;
}

// Load analytics page data: summary + prediction and render charts
function loadAnalytics(){
	// fetch summary first
	fetch('/api/summary', buildAuthOptions())
	.then(res => {
		if(res.status === 401) throw new Error('not-auth');
		return res.json();
	})
	.then(data => {
		// total
		const totalEl = document.getElementById('total-spent');
		if(totalEl) totalEl.textContent = (data.total || 0).toFixed(2);

		// top merchant
		const topEl = document.getElementById('top-merchant');
		if(topEl){
			const top = (data.top_merchants && data.top_merchants.length) ? data.top_merchants[0] : null;
			topEl.textContent = top ? `${top.merchant} — ${top.total.toFixed(2)}` : '—';
		}

		// category chart
		const catLabels = data.by_category.map(c => c.category);
		const catData = data.by_category.map(c => c.total);
		if(document.getElementById('categoryChart')){
			const ctx = document.getElementById('categoryChart').getContext('2d');
			if(window._analyticsCat) window._analyticsCat.destroy();
			window._analyticsCat = new Chart(ctx, {
				type: 'doughnut',
				data: { labels: catLabels, datasets: [{ data: catData, backgroundColor: generateColors(catData.length) }] },
				options: { plugins: { legend: { position: 'bottom' } } }
			});
		}

		// monthly chart
		const monthLabels = data.monthly.map(m => m.month);
		const monthData = data.monthly.map(m => m.total);
		if(document.getElementById('monthlyChart')){
			const ctx2 = document.getElementById('monthlyChart').getContext('2d');
			if(window._analyticsMonth) window._analyticsMonth.destroy();
			window._analyticsMonth = new Chart(ctx2, {
				type: 'line',
				data: { labels: monthLabels, datasets: [{ label: 'Spent', data: monthData, fill: true, backgroundColor: 'rgba(79,70,229,0.12)', borderColor: 'rgba(79,70,229,1)'}] },
				options: { scales: { y: { beginAtZero: true } } }
			});
		}
	})
	.catch(err => {
		if(err.message === 'not-auth') window.location = '/login';
		else console.error(err);
	});

	// fetch prediction separately
	fetch('/api/predict', buildAuthOptions())
	.then(res => {
		if(res.status === 401) throw new Error('not-auth');
		return res.json();
	})
	.then(p => {
		const predEl = document.getElementById('prediction');
		if(predEl) predEl.textContent = (p.prediction || 0).toFixed(2) + ' (' + (p.method || '') + ')';
	}).catch(err => {
		if(err.message === 'not-auth') window.location = '/login';
		else console.error(err);
	});
}

// Initialize charts and table on page load
document.addEventListener('DOMContentLoaded', function(){
	if(document.getElementById('expenseBody')) loadExpenses();
	// If we have budget controls, load budget first then summary so we can compare totals
	if(document.getElementById('budgetAmount')){
		loadBudget().then(()=>{
			if(document.getElementById('categoryChart')) loadSummary();
		});
		const btn = document.getElementById('setBudgetBtn');
		if(btn) btn.addEventListener('click', setBudget);
	} else {
		if(document.getElementById('categoryChart')) loadSummary();
	}
});

// --- Tabs and Add-Expense form integration on index page ---
function showTab(id){
	const sections = ['dashboardSection','addSection','viewSection'];
	sections.forEach(s => {
		const el = document.getElementById(s);
		if(!el) return;
		el.style.display = (s === id) ? 'block' : 'none';
	});
	// load content for the shown tab
	if(id === 'viewSection'){
		loadBudget();
		loadSummary();
		loadExpenses();
	}
	if(id === 'dashboardSection'){
		loadBudget();
		loadSummary();
	}
}

function initTabs(){
	document.querySelectorAll('.tab-btn').forEach(btn=>{
		btn.addEventListener('click', ()=>{
			const target = btn.getAttribute('data-tab');
			showTab(target);
		});
	});
}

function initAddExpenseForm(){
	const form = document.getElementById('expenseForm');
	if(!form) return;
	form.addEventListener('submit', function(e){
		e.preventDefault();
		const amount = document.getElementById('amountInput').value;
		const category = document.getElementById('categoryInput').value;
		const note = document.getElementById('noteInput').value;
		const date = document.getElementById('dateInput').value;
		const msg = document.getElementById('addMsg');

		fetch('/add-expense', buildAuthOptions('POST', {amount, category, note, date})).then(r=>{
			if(r.status === 401) throw new Error('not-auth');
			if(!r.ok) return r.json().then(j=>{ throw new Error(j.error||'failed') });
			return r.json();
		}).then(j=>{
			if(msg) msg.textContent = 'Added';
			// clear form
			form.reset();
			// switch to view tab and refresh
			showTab('viewSection');
			loadExpenses();
			loadSummary();
			setTimeout(()=>{ if(msg) msg.textContent = '' }, 1500);
		}).catch(e=>{
			if(e.message === 'not-auth') window.location = '/login';
			else if(msg) msg.textContent = 'Error: ' + e.message;
		});
	});
}

// initialize tabs and form after DOM ready
document.addEventListener('DOMContentLoaded', function(){
	initTabs();
	initAddExpenseForm();
	// show dashboard by default
	showTab('dashboardSection');
});
