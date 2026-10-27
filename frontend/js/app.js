// PetCare Spa Frontend Management JS (KT2 - Nhóm 6)
const API_BASE = window.location.origin;
let authToken = localStorage.getItem("petcare_token") || null;
let currentRole = localStorage.getItem("petcare_role") || null;
let currentUserName = localStorage.getItem("petcare_name") || null;

let cachedPets = [];
let cachedOwners = [];
let cachedServices = [];
let cachedAppointments = [], cachedVaccines = [];
let editOwnerId = null, editPetId = null, editServiceId = null, editPackageId = null, editAppointmentId = null, editVaccineId = null;

// INIT
document.addEventListener("DOMContentLoaded", () => {
    if (authToken) {
        showApp();
    } else {
        showLogin();
    }
});

function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    const msg = document.getElementById("toastMsg");
    const icon = document.getElementById("toastIcon");

    msg.innerText = message;
    if (isError) {
        toast.classList.replace("bg-slate-900", "bg-rose-900");
        icon.className = "fa-solid fa-circle-exclamation text-rose-400 text-base";
    } else {
        toast.classList.replace("bg-rose-900", "bg-slate-900");
        icon.className = "fa-solid fa-circle-check text-emerald-400 text-base";
    }

    toast.classList.add("toast-show");
    setTimeout(() => {
        toast.classList.remove("toast-show");
    }, 3500);
}

function fillLogin(user, pass) {
    document.getElementById("loginUser").value = user;
    document.getElementById("loginPass").value = pass;
}

async function handleLogin(e) {
    e.preventDefault();
    const user = document.getElementById("loginUser").value;
    const pass = document.getElementById("loginPass").value;

    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: user, password: pass })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Đăng nhập thất bại");

        authToken = data.access_token;
        currentRole = data.role;
        currentUserName = data.full_name;

        localStorage.setItem("petcare_token", authToken);
        localStorage.setItem("petcare_role", currentRole);
        localStorage.setItem("petcare_name", currentUserName);

        showToast(`Đăng nhập thành công! Xin chào ${currentUserName}`);
        showApp();
    } catch (err) {
        showToast(err.message, true);
    }
}

function handleLogout() {
    authToken = null;
    currentRole = null;
    currentUserName = null;
    localStorage.clear();
    showLogin();
    showToast("Đã đăng xuất");
}

function showLogin() {
    document.getElementById("loginScreen").classList.remove("hidden");
    document.getElementById("mainApp").classList.add("hidden");
    document.getElementById("btnLogout").classList.add("hidden");
    document.getElementById("userName").innerText = "Chưa đăng nhập";
    document.getElementById("userRole").innerText = "Guest";
}

async function showApp() {
    document.getElementById("loginScreen").classList.add("hidden");
    document.getElementById("mainApp").classList.remove("hidden");
    document.getElementById("btnLogout").classList.remove("hidden");
    document.getElementById("userName").innerText = currentUserName;
    document.getElementById("userRole").innerText = currentRole;

    await preloadData();
    switchTab("dashboard");
}

function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
    };
}

// TAB SWITCHING
function switchTab(tabName) {
    const tabs = ["dashboard", "appointments", "pets", "services", "health", "vaccine", "invoices", "ai"];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        const panel = document.getElementById(`panel-${t}`);
        if (t === tabName) {
            btn.classList.add("active-tab");
            panel.classList.remove("hidden");
        } else {
            btn.classList.remove("active-tab");
            panel.classList.add("hidden");
        }
    });

    if (tabName === "dashboard") loadDashboardStats();
    if (tabName === "appointments") loadAppointments();
    if (tabName === "pets") loadPets();
    if (tabName === "services") loadServices();
    if (tabName === "health") loadHealthRecords();
    if (tabName === "vaccine") loadVaccines();
    if (tabName === "invoices") loadInvoices();
    if (tabName === "ai") loadAiTab();
}

// PRELOAD
async function preloadData() {
    try {
        const [petsRes, ownersRes, srvRes] = await Promise.all([
            fetch(`${API_BASE}/api/pets`, { headers: getAuthHeaders() }),
            fetch(`${API_BASE}/api/owners`, { headers: getAuthHeaders() }),
            fetch(`${API_BASE}/api/services`, { headers: getAuthHeaders() })
        ]);
        cachedPets = await petsRes.json();
        cachedOwners = await ownersRes.json();
        cachedServices = await srvRes.json();
        populateDropdowns();
    } catch (err) {
        console.error("Lỗi tải cache:", err);
    }
}

function populateDropdowns() {
    // App modal dropdowns
    const petSelect = document.getElementById("appPetSelect");
    if (petSelect) {
        petSelect.innerHTML = cachedPets.map(p => `<option value="${p.pet_id}">[#${p.pet_id}] ${p.pet_name} (${p.breed || p.pet_type})</option>`).join("");
    }
    const srvSelect = document.getElementById("appServiceSelect");
    if (srvSelect) {
        srvSelect.innerHTML = cachedServices.map(s => `<option value="${s.service_id}">${s.service_name} (${s.duration_minutes}p - ${s.price.toLocaleString()}đ)</option>`).join("");
    }
    const ownerSelect = document.getElementById("petOwnerSelect");
    if (ownerSelect) {
        ownerSelect.innerHTML = cachedOwners.map(o => `<option value="${o.owner_id}">#${o.owner_id} - ${o.full_name} (${o.phone})</option>`).join("");
    }
}

// 1. DASHBOARD STATS
async function loadDashboardStats() {
    try {
        const res = await fetch(`${API_BASE}/api/analytics/dashboard`, { headers: getAuthHeaders() });
        const data = await res.json();
        document.getElementById("statRevenue").innerText = `${data.total_revenue.toLocaleString()} đ`;
        document.getElementById("statPets").innerText = `${data.total_pets} Thú cưng`;
        document.getElementById("statOwners").innerText = `${data.total_owners} Chủ nuôi đã lưu`;
        document.getElementById("statAppointments").innerText = `${data.total_appointments}`;
        document.getElementById("statPendingApps").innerText = `${data.pending_appointments} ca đang chờ`;
        document.getElementById("statRetention").innerText = `${data.retention_rate}%`;
        document.getElementById("statDebt").innerText = `${(data.total_debt || 0).toLocaleString()} đ`;
        loadDashboardExtras();
    } catch (err) {
        console.error("Dashboard stats error:", err);
    }
}

// 2. APPOINTMENTS & COLLISION CHECKING
async function loadAppointments() {
    try {
        const date = document.getElementById("filterAppDate").value;
        const groomer = document.getElementById("filterAppGroomer").value;
        const status = document.getElementById("filterAppStatus").value;

        let url = `${API_BASE}/api/appointments?`;
        if (date) url += `date=${date}&`;
        if (groomer) url += `groomer=${encodeURIComponent(groomer)}&`;
        if (status) url += `status=${status}&`;

        const res = await fetch(url, { headers: getAuthHeaders() });
        const data = await res.json();

        if (!res.ok) throw new Error();
        cachedAppointments = data;
        const tbody = document.getElementById("appointmentTableBody");
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-slate-400">Không tìm thấy lịch hẹn phù hợp</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(a => {
            const pet = cachedPets.find(p => p.pet_id === a.pet_id) || { pet_name: `Bé #${a.pet_id}`, breed: "" };
            const srv = cachedServices.find(s => s.service_id === a.service_id) || { service_name: `Dịch vụ #${a.service_id}` };
            
            let statusBadge = `<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-semibold text-[10px]">Chờ phục vụ</span>`;
            if (a.status === "COMPLETED") statusBadge = `<span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold text-[10px]">Đã hoàn tất</span>`;
            if (a.status === "CANCELLED") statusBadge = `<span class="bg-rose-100 text-rose-800 px-2 py-0.5 rounded font-semibold text-[10px]">Đã hủy</span>`;

            return `
                <tr class="border-b border-slate-100 hover:bg-slate-50 transition">
                    <td class="p-3 font-bold text-slate-700">#LH${a.appointment_id}</td>
                    <td class="p-3">
                        <strong class="text-blue-900">${pet.pet_name}</strong>
                        <div class="text-[10px] text-slate-500">${pet.breed}</div>
                    </td>
                    <td class="p-3 text-slate-600">${srv.service_name}</td>
                    <td class="p-3 font-medium text-slate-800">
                        <i class="fa-solid fa-user-gear text-slate-400 mr-1"></i> ${a.groomer_name}
                    </td>
                    <td class="p-3">
                        <div>📅 ${a.appointment_date}</div>
                        <div class="text-[11px] font-semibold text-slate-600">⏰ ${a.start_time} - ${a.end_time}</div>
                    </td>
                    <td class="p-3">${statusBadge}</td>
                    <td class="p-3 text-right space-x-1">
                        ${a.status === "CONFIRMED" ? `
                            <button onclick="openAppointmentModal(${a.appointment_id})" class="text-blue-700 px-2">Sửa</button>
                            ${currentRole !== "GROOMER" ? `<button onclick="cancelApp(${a.appointment_id})" class="text-rose-600 hover:bg-rose-50 px-2 py-1 rounded text-xs" title="Hủy lịch">
                                <i class="fa-solid fa-ban"></i>
                            </button>` : ""}
                        ` : ""}
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        showToast("Lỗi tải danh sách lịch hẹn", true);
    }
}

async function handleCreateAppointment(e) {
    e.preventDefault();
    const pet_id = parseInt(document.getElementById("appPetSelect").value);
    const service_id = parseInt(document.getElementById("appServiceSelect").value);
    const groomer_name = document.getElementById("appGroomerSelect").value;
    const appointment_date = document.getElementById("appDate").value;
    const start_time = document.getElementById("appStart").value;
    const end_time = document.getElementById("appEnd").value;
    const notes = document.getElementById("appNotes").value;

    try {
        const res = await fetch(`${API_BASE}/api/appointments${editAppointmentId ? `/${editAppointmentId}` : ""}`, {
            method: editAppointmentId ? "PUT" : "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({
                pet_id, service_id, groomer_name, appointment_date, start_time, end_time, notes
            })
        });
        const data = await res.json();
        if (!res.ok) {
            // Hiển thị chi tiết lỗi xung đột trùng lịch nếu có
            throw new Error(data.detail || "Không thể đặt lịch");
        }

        showToast(`Đặt lịch hẹn thành công cho ${groomer_name}!`);
        closeModal("modalAppointment");
        loadAppointments();
        loadDashboardStats();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function cancelApp(appId) {
    if (!confirm("Bạn có chắc chắn muốn hủy lịch hẹn này không?")) return;
    try {
        const res = await fetch(`${API_BASE}/api/appointments/${appId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Lỗi hủy lịch");
        showToast("Đã hủy lịch hẹn thành công");
        loadAppointments();
        loadDashboardStats();
    } catch (err) {
        showToast(err.message, true);
    }
}

// 3. PETS & OWNERS
async function loadPets() {
    try {
        const search = document.getElementById("searchPet").value;
        let url = `${API_BASE}/api/pets?`;
        if (search) url += `search=${encodeURIComponent(search)}`;

        const res = await fetch(url, { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error();
        renderOwners();

        const tbody = document.getElementById("petTableBody");
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-slate-400">Không tìm thấy thú cưng nào</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(p => `
            <tr class="border-b border-slate-100 hover:bg-slate-50 transition">
                <td class="p-3 font-bold text-slate-600">#TC${p.pet_id}</td>
                <td class="p-3 font-bold text-blue-900"><button type="button" onclick="showPetDetails(${p.pet_id})" class="text-blue-800 underline hover:text-blue-600">${escapeHtml(p.pet_name)}</button></td>
                <td class="p-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${p.pet_type === 'CHO' ? 'bg-amber-100 text-amber-800' : 'bg-purple-100 text-purple-800'}">
                        ${p.pet_type === 'CHO' ? 'Chó' : 'Mèo'}
                    </span>
                    <span class="text-slate-600 ml-1">${escapeHtml(p.breed || '')}</span>
                </td>
                <td class="p-3 text-slate-700">${p.weight} kg</td>
                <td class="p-3 text-slate-500 max-w-xs truncate">${escapeHtml(p.medical_history || 'Bình thường')}</td>
                <td class="p-3 font-medium text-slate-700"><button type="button" onclick="showOwnerDetails(${p.owner_id})" class="text-blue-800 underline hover:text-blue-600">${escapeHtml(cachedOwners.find(o => o.owner_id === p.owner_id)?.full_name || `Chủ #${p.owner_id}`)}</button></td>
                <td class="p-3 text-right">
                    ${currentRole !== "GROOMER" ? `<button onclick="openPetModal(${p.pet_id})" class="text-blue-700 px-2">Sửa</button>` : ""}
                    ${currentRole === "ADMIN" ? `<button onclick="deletePet(${p.pet_id})" class="text-rose-600 hover:bg-rose-50 px-2 py-1 rounded text-xs">
                        <i class="fa-solid fa-trash"></i>
                    </button>` : ""}
                </td>
            </tr>
        `).join("");
    } catch (err) {
        showToast("Lỗi tải thú cưng", true);
    }
}

async function handleCreateOwner(e) {
    e.preventDefault();
    const full_name = document.getElementById("ownerName").value;
    const phone = document.getElementById("ownerPhone").value;
    const address = document.getElementById("ownerAddress").value;
    const email = document.getElementById("ownerEmail").value;

    try {
        const res = await fetch(`${API_BASE}/api/owners${editOwnerId ? `/${editOwnerId}` : ""}`, {
            method: editOwnerId ? "PUT" : "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ full_name, phone, address, email })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Lỗi tạo chủ nuôi");
        showToast(`Đã thêm chủ nuôi: ${full_name}`);
        closeModal("modalOwner");
        await preloadData();
        renderOwners();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function handleCreatePet(e) {
    e.preventDefault();
    const owner_id = parseInt(document.getElementById("petOwnerSelect").value);
    const pet_name = document.getElementById("petName").value;
    const pet_type = document.getElementById("petType").value;
    const breed = document.getElementById("petBreed").value;
    const weight = parseFloat(document.getElementById("petWeight").value);
    const age = document.getElementById("petAge").value === "" ? null : parseInt(document.getElementById("petAge").value, 10);
    const medical_history = document.getElementById("petMedHistory").value;

    try {
        const res = await fetch(`${API_BASE}/api/pets${editPetId ? `/${editPetId}` : ""}`, {
            method: editPetId ? "PUT" : "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ owner_id, pet_name, pet_type, breed, weight, age, medical_history })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Lỗi tạo thú cưng");
        showToast(`Đã thêm thú cưng: ${pet_name}`);
        closeModal("modalPet");
        await preloadData();
        loadPets();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deletePet(petId) {
    if (!confirm("Bạn có chắc chắn muốn xóa thú cưng này?")) return;
    try {
        const res = await fetch(`${API_BASE}/api/pets/${petId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Lỗi xóa thú cưng");
        showToast("Đã xóa thú cưng");
        await preloadData();
        loadPets();
    } catch (err) {
        showToast(err.message, true);
    }
}

// 4. SERVICES & PACKAGES
let cachedPackages = [];

async function loadServices() {
    try {
        const res = await fetch(`${API_BASE}/api/services`, { headers: getAuthHeaders() });
        const data = await res.json();
        cachedServices = data;

        const container = document.getElementById("serviceCardsContainer");
        container.innerHTML = data.map(s => `
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow transition flex flex-col justify-between">
                <div>
                    <div class="flex justify-between items-start">
                        <h4 class="font-bold text-slate-800 text-sm">${escapeHtml(s.service_name)}</h4>
                        <span class="bg-blue-100 text-blue-900 font-bold px-2 py-0.5 rounded text-xs">${s.duration_minutes} phút</span>
                    </div>
                    <p class="text-xs text-slate-500 mt-2">${escapeHtml(s.description || 'Dịch vụ spa tiêu chuẩn')}</p>
                </div>
                <div class="mt-4 pt-3 border-t border-slate-100 flex justify-between items-center">
                    <span class="text-xs text-slate-400">Đơn giá trọn gói ${currentRole === "ADMIN" ? `<button onclick="openServiceModal(${s.service_id})" class="text-blue-700 ml-2">Sửa</button> <button onclick="deleteService(${s.service_id})" class="text-rose-600 ml-2">Xóa</button>` : ""}</span>
                    <strong class="text-base text-emerald-700">${s.price.toLocaleString()} đ</strong>
                </div>
            </div>
        `).join("");
        await loadPackages();
    } catch (err) {
        showToast("Lỗi tải danh mục dịch vụ", true);
    }
}

async function loadPackages() {
    const res = await fetch(`${API_BASE}/api/packages`, { headers: getAuthHeaders() });
    cachedPackages = await res.json();
    const box = document.getElementById("packageCardsContainer");
    if (!cachedPackages.length) {
        box.innerHTML = `<p class="text-xs text-slate-400">Chưa có gói dịch vụ nào</p>`;
        return;
    }
    box.innerHTML = cachedPackages.map(p => `
        <div class="bg-white p-5 rounded-xl border border-fuchsia-200 shadow-sm flex flex-col justify-between ${p.is_active ? '' : 'opacity-60'}">
            <div>
                <div class="flex justify-between items-start">
                    <h4 class="font-bold text-slate-800 text-sm">${escapeHtml(p.package_name)}</h4>
                    ${p.is_active ? '' : '<span class="text-[10px] bg-slate-200 px-2 py-0.5 rounded">Tạm ngưng</span>'}
                </div>
                <p class="text-xs text-slate-500 mt-1">${escapeHtml(p.description || '')}</p>
                <ul class="text-xs text-slate-600 mt-2 list-disc pl-4">
                    ${p.items.map(i => `<li>${escapeHtml(i.service_name)} × ${i.quantity}</li>`).join("")}
                </ul>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-100">
                <div class="flex justify-between items-center">
                    <span class="text-xs text-slate-400 line-through">${p.original_price.toLocaleString()} đ</span>
                    <strong class="text-base text-fuchsia-700">${p.price.toLocaleString()} đ</strong>
                </div>
                <div class="flex justify-between items-center mt-1">
                    <span class="text-[11px] text-emerald-700">Tiết kiệm ${p.saving.toLocaleString()} đ</span>
                    ${currentRole === "ADMIN" ? `<button onclick="openPackageModal(${p.package_id})" class="text-blue-700 mr-2">Sửa</button><button onclick="deletePackage(${p.package_id})" class="text-[11px] text-rose-600 hover:underline">Xóa gói</button>` : ""}
                </div>
            </div>
        </div>
    `).join("");
}

function openServiceModal(id = null) {
    editServiceId = id;
    ["svcName", "svcPrice", "svcDesc"].forEach(id => document.getElementById(id).value = "");
    document.getElementById("svcDuration").value = 60;
    if (id) { const s = cachedServices.find(x => x.service_id === id); if (!s) return; document.getElementById("svcName").value = s.service_name; document.getElementById("svcPrice").value = s.price; document.getElementById("svcDesc").value = s.description || ""; document.getElementById("svcDuration").value = s.duration_minutes; }
    openModal("modalService");
}

async function handleCreateService(e) {
    e.preventDefault();
    const body = {
        service_name: document.getElementById("svcName").value.trim(),
        duration_minutes: parseInt(document.getElementById("svcDuration").value, 10),
        price: parseFloat(document.getElementById("svcPrice").value),
        description: document.getElementById("svcDesc").value.trim() || null
    };
    await sendJson(editServiceId ? `/api/services/${editServiceId}` : "/api/services", editServiceId ? "PUT" : "POST", body, "Đã lưu dịch vụ", () => { closeModal("modalService"); preloadData(); loadServices(); });
}

function openPackageModal(id = null) {
    editPackageId = id;
    document.getElementById("pkgName").value = "";
    document.getElementById("pkgDesc").value = "";
    document.getElementById("pkgPrice").value = "";
    document.getElementById("pkgServiceList").innerHTML = cachedServices.map(s => `
        <label class="flex items-center gap-2">
            <input type="checkbox" class="pkg-check" data-id="${s.service_id}" data-price="${s.price}" onchange="updatePackageOriginal()">
            <span class="flex-1">${escapeHtml(s.service_name)} (${s.price.toLocaleString()} đ)</span>
            <input type="number" min="1" value="1" class="pkg-qty w-14 border rounded p-1" data-id="${s.service_id}" oninput="updatePackageOriginal()">
        </label>`).join("");
    if (id) { const p = cachedPackages.find(x => x.package_id === id); if (!p) return; document.getElementById("pkgName").value = p.package_name; document.getElementById("pkgDesc").value = p.description || ""; document.getElementById("pkgPrice").value = p.price; p.items.forEach(i => { const c = document.querySelector(`.pkg-check[data-id="${i.service_id}"]`); const q = document.querySelector(`.pkg-qty[data-id="${i.service_id}"]`); if (c && q) { c.checked = true; q.value = i.quantity; } }); }
    updatePackageOriginal();
    openModal("modalPackage");
}

function selectedPackageItems() {
    const items = [];
    document.querySelectorAll(".pkg-check").forEach(chk => {
        if (!chk.checked) return;
        const qty = parseInt(document.querySelector(`.pkg-qty[data-id="${chk.dataset.id}"]`).value, 10) || 1;
        items.push({ service_id: parseInt(chk.dataset.id, 10), quantity: Math.max(1, qty), price: parseFloat(chk.dataset.price) });
    });
    return items;
}

function updatePackageOriginal() {
    const total = selectedPackageItems().reduce((sum, i) => sum + i.price * i.quantity, 0);
    document.getElementById("pkgOriginal").textContent = `Giá lẻ: ${total.toLocaleString()} đ`;
}

async function handleCreatePackage(e) {
    e.preventDefault();
    const items = selectedPackageItems();
    if (!items.length) { showToast("Hãy chọn ít nhất một dịch vụ cho gói", true); return; }
    const body = {
        package_name: document.getElementById("pkgName").value.trim(),
        description: document.getElementById("pkgDesc").value.trim() || null,
        price: parseFloat(document.getElementById("pkgPrice").value),
        items: items.map(i => ({ service_id: i.service_id, quantity: i.quantity }))
    };
    await sendJson(editPackageId ? `/api/packages/${editPackageId}` : "/api/packages", editPackageId ? "PUT" : "POST", body, "Đã lưu gói dịch vụ", () => { closeModal("modalPackage"); loadPackages(); });
}

async function deletePackage(id) {
    if (!confirm("Xóa gói dịch vụ này?")) return;
    await sendJson(`/api/packages/${id}`, "DELETE", null, "Đã xóa gói", loadPackages);
}

// Hàm gửi JSON dùng chung: hiện toast lỗi theo detail của server
async function sendJson(path, method, body, okMsg, onOk) {
    try {
        const res = await fetch(`${API_BASE}${path}`, {
            method, headers: getAuthHeaders(), body: body === null ? undefined : JSON.stringify(body)
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            let msg = data.detail;
            if (Array.isArray(msg)) msg = msg.map(d => d.msg).join("; ");
            throw new Error(msg || "Thao tác thất bại");
        }
        showToast(okMsg);
        if (onOk) await onOk(data);
        return data;
    } catch (err) {
        showToast(err.message, true);
        return null;
    }
}

// 5. HEALTH RECORDS
let cachedCare = [];

async function loadHealthRecords() {
    try {
        const res = await fetch(`${API_BASE}/api/care-records`, { headers: getAuthHeaders() });
        const data = await res.json();
        cachedCare = data;
        const tbody = document.getElementById("healthTableBody");
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="p-4 text-center text-slate-400">Chưa có hồ sơ chăm sóc da lông nào</td></tr>`;
            return;
        }
        const petName = id => { const p = cachedPets.find(x => x.pet_id === id); return p ? p.pet_name : `Bé #${id}`; };
        tbody.innerHTML = data.map(r => `
            <tr class="border-b border-slate-100 hover:bg-slate-50 transition text-xs">
                <td class="p-3 font-bold text-slate-700">#HS${r.care_id}</td>
                <td class="p-3 font-semibold text-blue-900">${escapeHtml(petName(r.pet_id))}</td>
                <td class="p-3">${r.weight_after ? `${r.weight_after} kg` : '—'}</td>
                <td class="p-3 font-medium text-amber-900">${escapeHtml(r.skin_condition || 'Bình thường')}</td>
                <td class="p-3 text-slate-600">${escapeHtml(r.behavior_notes || '—')}</td>
                <td class="p-3 text-emerald-800 italic">${escapeHtml(r.advice || '—')}</td>
                <td class="p-3 text-slate-400">${new Date(r.record_date).toLocaleDateString()}</td>
                <td class="p-3 whitespace-nowrap">
                    <button onclick="openCareModal(${r.care_id})" class="text-blue-700 hover:underline mr-2">Sửa</button>
                    ${currentRole === "ADMIN" ? `<button onclick="deleteCare(${r.care_id})" class="text-rose-600 hover:underline">Xóa</button>` : ""}
                </td>
            </tr>
        `).join("");
    } catch (err) {
        showToast("Lỗi tải hồ sơ da lông", true);
    }
}

async function openCareModal(careId) {
    if (!cachedPets || cachedPets.length === 0) await preloadData();
    const sel = document.getElementById("carePetSelect");
    sel.innerHTML = cachedPets.map(p => `<option value="${p.pet_id}">[#${p.pet_id}] ${escapeHtml(p.pet_name)}</option>`).join("");
    const rec = careId ? cachedCare.find(r => r.care_id === careId) : null;
    document.getElementById("careId").value = rec ? rec.care_id : "";
    document.getElementById("careModalTitle").textContent = rec ? `Sửa Hồ Sơ #HS${rec.care_id}` : "Thêm Hồ Sơ Chăm Sóc";
    sel.value = rec ? rec.pet_id : sel.value;
    sel.disabled = !!rec;                         // không đổi thú cưng của hồ sơ đã có
    document.getElementById("careWeight").value = rec && rec.weight_after ? rec.weight_after : "";
    document.getElementById("careSkin").value = rec ? (rec.skin_condition || "") : "";
    document.getElementById("careBehavior").value = rec ? (rec.behavior_notes || "") : "";
    document.getElementById("careAdvice").value = rec ? (rec.advice || "") : "";
    openModal("modalCare");
}

async function handleSaveCare(e) {
    e.preventDefault();
    const id = document.getElementById("careId").value;
    const w = document.getElementById("careWeight").value;
    const fields = {
        weight_after: w ? parseFloat(w) : null,
        skin_condition: document.getElementById("careSkin").value.trim() || null,
        behavior_notes: document.getElementById("careBehavior").value.trim() || null,
        advice: document.getElementById("careAdvice").value.trim() || null
    };
    const done = () => { closeModal("modalCare"); loadHealthRecords(); };
    if (id) {
        await sendJson(`/api/care-records/${id}`, "PUT", fields, "Đã cập nhật hồ sơ", done);
    } else {
        const pet_id = parseInt(document.getElementById("carePetSelect").value, 10);
        await sendJson("/api/care-records", "POST", { pet_id, ...fields }, "Đã thêm hồ sơ chăm sóc", done);
    }
}

async function deleteCare(id) {
    if (!confirm(`Xóa hồ sơ #HS${id}?`)) return;
    await sendJson(`/api/care-records/${id}`, "DELETE", null, "Đã xóa hồ sơ", loadHealthRecords);
}

// 6. VACCINES
async function loadVaccines() {
    try {
        const res = await fetch(`${API_BASE}/api/vaccinations`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error();
        cachedVaccines = data;
        const tbody = document.getElementById("vaccineTableBody");
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-slate-400">Chưa có lịch nhắc tiêm phòng</td></tr>`;
            return;
        }
        tbody.innerHTML = data.map(v => `
            <tr class="border-b border-slate-100 hover:bg-slate-50 transition text-xs">
                <td class="p-3 font-bold text-slate-600">#TC${v.reminder_id}</td>
                <td class="p-3 font-semibold text-blue-900">Bé #${v.pet_id}</td>
                <td class="p-3 font-medium text-slate-800">${escapeHtml(v.vaccine_name)}</td>
                <td class="p-3 text-slate-500">${v.last_date || 'Chưa ghi'}</td>
                <td class="p-3 font-bold text-amber-700">📅 ${v.next_due_date}</td>
                <td class="p-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${v.status === 'DONE' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                        ${v.status === 'DONE' ? 'Đã tiêm' : 'Chờ tiêm'}
                    </span>
                </td>
                <td class="p-3 text-right">
                    ${currentRole !== 'GROOMER' ? `<button onclick="openVaccineModal(${v.reminder_id})" class="text-blue-700 px-2">Sửa</button><button onclick="deleteVaccine(${v.reminder_id})" class="text-rose-700 px-2">Xóa</button>` : ''}
                    ${currentRole !== 'GROOMER' && v.status === 'PENDING' ? `
                        <button onclick="markVaccineDone(${v.reminder_id})" class="bg-emerald-50 hover:bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs">
                            <i class="fa-solid fa-check mr-1"></i> Đã tiêm
                        </button>
                    ` : ""}
                </td>
            </tr>
        `).join("");
    } catch (err) {
        showToast("Lỗi tải lịch tiêm nhắc", true);
    }
}

async function markVaccineDone(reminderId) {
    try {
        const res = await fetch(`${API_BASE}/api/vaccinations/${reminderId}/done`, {
            method: "PUT",
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error("Lỗi cập nhật mũi tiêm");
        showToast("Đã cập nhật trạng thái tiêm phòng!");
        loadVaccines();
    } catch (err) {
        showToast(err.message, true);
    }
}

// 7. INVOICES & DEBT
let cachedInvoices = [];
const INVOICE_STATUS = {
    PAID: ["Đã thu đủ", "bg-emerald-100 text-emerald-800"],
    PARTIAL: ["Còn nợ", "bg-amber-100 text-amber-800"],
    UNPAID: ["Chưa thu", "bg-rose-100 text-rose-800"],
    CANCELLED: ["Đã hủy", "bg-slate-200 text-slate-600"]
};

async function loadInvoices() {
    try {
        const st = document.getElementById("invoiceStatusFilter").value;
        const res = await fetch(`${API_BASE}/api/invoices${st ? `?status=${st}` : ""}`, { headers: getAuthHeaders() });
        const data = await res.json();
        cachedInvoices = data;
        const tbody = document.getElementById("invoiceTableBody");
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="11" class="p-4 text-center text-slate-400">Chưa có hóa đơn nào</td></tr>`;
            return;
        }
        tbody.innerHTML = data.map(inv => {
            const [label, cls] = INVOICE_STATUS[inv.status] || [inv.status, "bg-slate-100"];
            const canPay = inv.remaining > 0 && inv.status !== "CANCELLED";
            return `
            <tr class="border-b border-slate-100 hover:bg-slate-50 transition text-xs">
                <td class="p-3 font-bold text-slate-800">#HD${inv.invoice_id}</td>
                <td class="p-3">Chủ #${inv.owner_id}</td>
                <td class="p-3 text-blue-900">${inv.appointment_id ? `#LH${inv.appointment_id}` : 'Trực tiếp'}</td>
                <td class="p-3 text-slate-500">${new Date(inv.created_at).toLocaleDateString()}</td>
                <td class="p-3">${inv.total_amount.toLocaleString()} đ</td>
                <td class="p-3 text-rose-600">-${inv.discount.toLocaleString()} đ</td>
                <td class="p-3 font-black text-slate-800">${inv.final_amount.toLocaleString()} đ</td>
                <td class="p-3 text-emerald-700 font-semibold">${inv.paid_amount.toLocaleString()} đ</td>
                <td class="p-3 ${inv.remaining > 0 ? 'text-rose-600 font-bold' : 'text-slate-400'}">${inv.remaining.toLocaleString()} đ</td>
                <td class="p-3"><span class="${cls} px-2 py-0.5 rounded font-bold text-[10px]">${label}</span></td>
                <td class="p-3 whitespace-nowrap">
                    ${canPay && currentRole !== "GROOMER" ? `<button onclick="openPaymentModal(${inv.invoice_id})" class="text-emerald-700 hover:underline mr-2">Thu tiền</button>` : ""}
                    ${currentRole === "ADMIN" && inv.status !== "CANCELLED" ? `<button onclick="cancelInvoice(${inv.invoice_id})" class="text-rose-600 hover:underline">Hủy</button>` : ""}
                </td>
            </tr>`;
        }).join("");
    } catch (err) {
        showToast("Lỗi tải hóa đơn", true);
    }
}

async function openInvoiceModal() {
    if (!cachedOwners.length || !cachedServices.length) await preloadData();
    document.getElementById("invOwnerSelect").innerHTML = cachedOwners.map(o => `<option value="${o.owner_id}">#${o.owner_id} - ${escapeHtml(o.full_name)}</option>`).join("");
    document.getElementById("invServiceSelect").innerHTML = cachedServices.map(s => `<option value="${s.service_id}">${escapeHtml(s.service_name)} (${s.price.toLocaleString()} đ)</option>`).join("");
    document.getElementById("invQty").value = 1;
    document.getElementById("invDiscount").value = 0;
    const paid = document.getElementById("invPaid");
    paid.value = ""; delete paid.dataset.touched;
    updateInvoicePreview();
    openModal("modalInvoice");
}

function invoiceDraft() {
    const srv = cachedServices.find(s => s.service_id === parseInt(document.getElementById("invServiceSelect").value, 10));
    const qty = Math.max(1, parseInt(document.getElementById("invQty").value, 10) || 1);
    const discount = Math.max(0, parseFloat(document.getElementById("invDiscount").value) || 0);
    const subtotal = srv ? srv.price * qty : 0;
    return { srv, qty, discount, subtotal, final: Math.max(0, subtotal - discount) };
}

function updateInvoicePreview() {
    const d = invoiceDraft();
    const paidEl = document.getElementById("invPaid");
    if (!paidEl.dataset.touched) paidEl.value = d.final;      // mặc định thanh toán đủ, sửa số nhỏ hơn để ghi nợ
    const paid = parseFloat(paidEl.value) || 0;
    document.getElementById("invPreview").textContent =
        `Tạm tính: ${d.subtotal.toLocaleString()} đ · Phải thu: ${d.final.toLocaleString()} đ · Còn nợ: ${Math.max(0, d.final - paid).toLocaleString()} đ`;
}

async function handleCreateInvoice(e) {
    e.preventDefault();
    const d = invoiceDraft();
    const body = {
        owner_id: parseInt(document.getElementById("invOwnerSelect").value, 10),
        discount: d.discount,
        payment_method: document.getElementById("invMethod").value,
        paid_amount: parseFloat(document.getElementById("invPaid").value) || 0,
        items: [{ service_id: d.srv.service_id, quantity: d.qty }]
    };
    await sendJson("/api/invoices", "POST", body, "Đã lập hóa đơn", () => { closeModal("modalInvoice"); loadInvoices(); });
}

function openPaymentModal(invoiceId) {
    const inv = cachedInvoices.find(i => i.invoice_id === invoiceId);
    if (!inv) return;
    document.getElementById("payInvoiceId").value = invoiceId;
    document.getElementById("payModalTitle").textContent = `Thu tiền hóa đơn #HD${invoiceId}`;
    document.getElementById("payRemaining").textContent = `Còn nợ: ${inv.remaining.toLocaleString()} đ`;
    document.getElementById("payAmount").value = inv.remaining;
    document.getElementById("payAmount").max = inv.remaining;
    document.getElementById("payCode").value = "";
    openModal("modalPayment");
}

async function handleAddPayment(e) {
    e.preventDefault();
    const id = document.getElementById("payInvoiceId").value;
    const body = {
        amount: parseFloat(document.getElementById("payAmount").value),
        payment_method: document.getElementById("payMethod").value,
        transaction_code: document.getElementById("payCode").value.trim() || null
    };
    await sendJson(`/api/invoices/${id}/payments`, "POST", body, "Đã ghi nhận thanh toán", () => { closeModal("modalPayment"); loadInvoices(); });
}

async function cancelInvoice(id) {
    if (!confirm(`Hủy hóa đơn #HD${id}? Hóa đơn hủy sẽ không tính vào doanh thu.`)) return;
    await sendJson(`/api/invoices/${id}/cancel`, "POST", null, "Đã hủy hóa đơn", loadInvoices);
}

// Thống kê phụ trên dashboard
async function loadDashboardExtras() {
    try {
        const [svcRes, revRes] = await Promise.all([
            fetch(`${API_BASE}/api/analytics/services`, { headers: getAuthHeaders() }),
            fetch(`${API_BASE}/api/analytics/revenue?period=month`, { headers: getAuthHeaders() })
        ]);
        const svc = await svcRes.json();
        const rev = await revRes.json();
        document.getElementById("serviceStatsBody").innerHTML = svc.map(r => `
            <tr class="border-t border-slate-100">
                <td class="p-2">${escapeHtml(r.service_name)}</td><td class="p-2 font-bold">${r.booked_count}</td>
                <td class="p-2">${r.completed_count}</td><td class="p-2 text-emerald-700">${r.revenue.toLocaleString()} đ</td>
            </tr>`).join("") || `<tr><td colspan="4" class="p-3 text-slate-400">Chưa có dữ liệu</td></tr>`;
        document.getElementById("revenueByMonth").innerHTML = rev.length
            ? rev.map(r => `<div class="flex justify-between"><span>${escapeHtml(r.period)}</span><b>${r.revenue.toLocaleString()} đ</b></div>`).join("")
            : "<span class='text-slate-400'>Chưa có doanh thu</span>";
    } catch (e) { console.error("Dashboard extras error:", e); }
}

// MODAL CONTROLS
function openModal(modalId) {
    document.getElementById(modalId).classList.remove("hidden");
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add("hidden");
}


// =====================================================================
// 8. TRỢ LÝ AI (Gemini)
// =====================================================================
async function loadAiTab() {
    if (!cachedPets || cachedPets.length === 0) await preloadData();
    const sel = document.getElementById("aiPetSelect");
    const prev = sel.value;
    sel.innerHTML = cachedPets.map(p => `<option value="${p.pet_id}">[#${p.pet_id}] ${escapeHtml(p.pet_name)} (${escapeHtml(p.breed || p.pet_type)})</option>`).join("");
    if (prev) sel.value = prev;
    try {
        const res = await fetch(`${API_BASE}/api/ai/status`, { headers: getAuthHeaders() });
        const st = await res.json();
        const badge = document.getElementById("aiStatusBadge");
        badge.textContent = st.configured ? `Gemini: ${st.model}` : "Chế độ dự phòng (chưa cấu hình GEMINI_API_KEY)";
        badge.className = "text-[11px] px-2 py-1 rounded-full " + (st.configured ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700");
    } catch (e) { /* bỏ qua */ }
    if (currentRole === "ADMIN") loadAiAdminStats();
}

async function loadAiAdminStats() {
    try {
        const res = await fetch(`${API_BASE}/api/ai/logs?limit=1`, { headers: getAuthHeaders() });
        if (!res.ok) return;
        const d = await res.json();
        const card = (label, value) => `<div class="bg-slate-50 border rounded-lg p-3"><div class="text-slate-500">${label}</div><div class="text-lg font-black text-slate-800">${escapeHtml(value)}</div></div>`;
        const src = d.by_source || {};
        document.getElementById("aiAdminStats").innerHTML =
            card("Tổng lượt gọi AI", d.total) +
            card("Do Gemini trả lời", src.gemini || 0) +
            card("Rào chắn chặn / dự phòng", `${src.guardrail || 0} / ${src.fallback || 0}`) +
            card("Độ trễ trung bình", `${d.avg_latency_ms} ms`);
        document.getElementById("aiAdminBox").classList.remove("hidden");
    } catch (e) { /* bỏ qua */ }
}

function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function selectedAiPetId() {
    const v = document.getElementById("aiPetSelect").value;
    if (!v) { showToast("Vui lòng chọn thú cưng", true); return null; }
    return parseInt(v, 10);
}

async function aiCall(path, body, btnId, outId) {
    const btn = document.getElementById(btnId);
    const out = document.getElementById(outId);
    const oldLabel = btn.textContent;
    btn.disabled = true; btn.textContent = "Đang xử lý...";
    out.textContent = "";
    try {
        const res = await fetch(`${API_BASE}${path}`, {
            method: "POST",
            headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
            body: body ? JSON.stringify(body) : undefined
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const msg = typeof data.detail === "string" ? data.detail : "Yêu cầu không hợp lệ";
            showToast(msg, true);
            return;
        }
        renderAiResult(out, data);
    } catch (e) {
        showToast("Không kết nối được máy chủ", true);
    } finally {
        btn.disabled = false; btn.textContent = oldLabel;
    }
}

// Dùng textContent để nội dung AI không thể chèn HTML/script (chống XSS)
function renderAiResult(container, data) {
    container.textContent = "";
    const box = document.createElement("div");
    box.className = "border rounded-md p-3 space-y-2 " + (data.need_vet ? "bg-red-50 border-red-300" : "bg-slate-50 border-slate-200");

    if (data.need_vet) {
        const alert = document.createElement("div");
        alert.className = "text-xs font-bold text-red-700";
        alert.textContent = "Nên liên hệ bác sĩ thú y";
        box.appendChild(alert);
    }
    const content = document.createElement("div");
    content.className = "whitespace-pre-wrap text-slate-800";
    content.textContent = data.content;
    box.appendChild(content);

    const meta = document.createElement("div");
    meta.className = "flex items-center justify-between gap-2 text-[11px] text-slate-500";
    const labels = { gemini: "Tạo bởi Gemini", fallback: "Mẫu dự phòng (AI chưa sẵn sàng)", guardrail: "Câu trả lời an toàn cố định" };
    const src = document.createElement("span");
    src.textContent = labels[data.source] || data.source;
    const copy = document.createElement("button");
    copy.className = "text-blue-700 hover:underline";
    copy.textContent = "Sao chép";
    copy.onclick = () => { navigator.clipboard.writeText(data.content).then(() => showToast("Đã sao chép")); };
    meta.append(src, copy);
    box.appendChild(meta);

    const warn = document.createElement("div");
    warn.className = "text-[11px] text-amber-800 italic border-t border-amber-200 pt-2";
    warn.textContent = data.warning;
    box.appendChild(warn);
    container.appendChild(box);
}

function runAiReminder() {
    const id = selectedAiPetId(); if (id === null) return;
    const kind = document.getElementById("aiReminderKind").value;
    aiCall("/api/ai/reminder", { pet_id: id, kind }, "btnAiReminder", "aiReminderOut");
}

function runAiSummary() {
    const id = selectedAiPetId(); if (id === null) return;
    aiCall(`/api/ai/summary/${id}`, null, "btnAiSummary", "aiSummaryOut");
}

function runAiAsk() {
    const q = document.getElementById("aiQuestion").value.trim();
    if (q.length < 3) { showToast("Vui lòng nhập câu hỏi (ít nhất 3 ký tự)", true); return; }
    const v = document.getElementById("aiPetSelect").value;
    aiCall("/api/ai/ask", { question: q, pet_id: v ? parseInt(v, 10) : null }, "btnAiAsk", "aiAskOut");
}

function openAppointmentModal(id = null) {
    editAppointmentId = id; document.getElementById('appPetSelect').disabled = !!id; document.getElementById('appServiceSelect').disabled = !!id; const form = document.querySelector('#modalAppointment form'); form.reset(); populateDropdowns();
    if (id) { const a = cachedAppointments.find(x => x.appointment_id === id); if (!a) return; for (const [key, field] of Object.entries({pet_id:'appPetSelect',service_id:'appServiceSelect',groomer_name:'appGroomerSelect',appointment_date:'appDate',start_time:'appStart',end_time:'appEnd',notes:'appNotes'})) document.getElementById(field).value = a[key] ?? ''; }
    openModal('modalAppointment');
}
function openOwnerModal(id = null) {
    editOwnerId = id; document.querySelector('#modalOwner form').reset();
    if (id) { const o = cachedOwners.find(x => x.owner_id === id); if (!o) return; for (const [key, field] of Object.entries({full_name:'ownerName',phone:'ownerPhone',address:'ownerAddress',email:'ownerEmail'})) document.getElementById(field).value = o[key] ?? ''; }
    openModal('modalOwner');
}
function renderOwners() {
    document.getElementById('ownerList').innerHTML = cachedOwners.map(o => `<div class="border-b py-2 text-sm flex justify-between"><span><button type="button" onclick="showOwnerDetails(${o.owner_id})" class="text-blue-800 underline">${escapeHtml(o.full_name)}</button> · ${escapeHtml(o.phone)}</span><span>${currentRole !== 'GROOMER' ? `<button class="text-blue-700 mr-2" onclick="openOwnerModal(${o.owner_id})">Sửa</button>` : ''}${currentRole === 'ADMIN' ? `<button class="text-rose-700" onclick="deleteOwner(${o.owner_id})">Xóa</button>` : ''}</span></div>`).join('') || 'Chưa có chủ nuôi';
}
async function deleteOwner(id) { if (confirm('Xóa chủ nuôi này?')) await sendJson(`/api/owners/${id}`, 'DELETE', null, 'Đã xóa chủ nuôi', async () => { await preloadData(); renderOwners(); }); }
function openPetModal(id = null) {
    editPetId = id; document.querySelector('#modalPet form').reset(); populateDropdowns();
    if (id) { const p = cachedPets.find(x => x.pet_id === id); if (!p) return; for (const [key, field] of Object.entries({owner_id:'petOwnerSelect',pet_name:'petName',pet_type:'petType',breed:'petBreed',weight:'petWeight',age:'petAge',medical_history:'petMedHistory'})) document.getElementById(field).value = p[key] ?? ''; }
    openModal('modalPet');
}
async function deleteService(id) { if (confirm('Xóa dịch vụ này?')) await sendJson(`/api/services/${id}`, 'DELETE', null, 'Đã xóa dịch vụ', async () => { await preloadData(); await loadServices(); }); }
function openVaccineModal(id = null) {
    editVaccineId = id; document.querySelector('#modalVaccine form').reset();
    document.getElementById('vacPet').innerHTML = cachedPets.map(p => `<option value="${p.pet_id}">${escapeHtml(p.pet_name)}</option>`).join('');
    if (id) { const v = cachedVaccines.find(x => x.reminder_id === id); if (!v) return; for (const [key, field] of Object.entries({pet_id:'vacPet',vaccine_name:'vacName',last_date:'vacLast',next_due_date:'vacDue',status:'vacStatus'})) document.getElementById(field).value = v[key] ?? ''; }
    openModal('modalVaccine');
}
async function saveVaccine(e) {
    e.preventDefault(); const body = {pet_id: Number(document.getElementById('vacPet').value), vaccine_name: document.getElementById('vacName').value.trim(), last_date: document.getElementById('vacLast').value || null, next_due_date: document.getElementById('vacDue').value, status: document.getElementById('vacStatus').value};
    await sendJson(editVaccineId ? `/api/vaccinations/${editVaccineId}` : '/api/vaccinations', editVaccineId ? 'PUT' : 'POST', body, 'Đã lưu lịch nhắc', () => { closeModal('modalVaccine'); loadVaccines(); });
}
async function deleteVaccine(id) { if (confirm('Xóa lịch nhắc này?')) await sendJson(`/api/vaccinations/${id}`, 'DELETE', null, 'Đã xóa lịch nhắc', loadVaccines); }

// Chi tiết luôn lấy từ API để phản ánh dữ liệu mới và quyền xem của người đăng nhập.
async function showPetDetails(petId) {
    try {
        const response = await fetch(`${API_BASE}/api/pets/${petId}`, {headers: getAuthHeaders()});
        if (!response.ok) throw new Error("Không tải được thông tin thú cưng");
        const pet = await response.json();
        await showOwnerDetails(pet.owner_id, petId);
    } catch (err) { showToast(err.message, true); }
}

async function showOwnerDetails(ownerId, selectedPetId = null) {
    try {
        const [ownerResponse, petsResponse] = await Promise.all([
            fetch(`${API_BASE}/api/owners/${ownerId}`, {headers: getAuthHeaders()}),
            fetch(`${API_BASE}/api/pets?owner_id=${ownerId}`, {headers: getAuthHeaders()})
        ]);
        if (!ownerResponse.ok || !petsResponse.ok) throw new Error("Không tải được thông tin chủ nuôi và thú cưng");
        const owner = await ownerResponse.json();
        let pets = await petsResponse.json();
        if (selectedPetId !== null) pets = pets.filter(p => p.pet_id === selectedPetId);
        const item = (label, value) => `<div><dt class="text-slate-500">${label}</dt><dd class="font-medium break-words">${escapeHtml(value === null || value === undefined || value === '' ? 'Chưa cập nhật' : value)}</dd></div>`;
        const contacts = currentRole === 'GROOMER' ? item('Số điện thoại', owner.phone) : item('Số điện thoại', owner.phone) + item('Email', owner.email) + item('Địa chỉ', owner.address);
        const petCards = pets.map(p => `<section class="border rounded-lg p-3"><h4 class="font-bold text-blue-900 mb-2">${escapeHtml(p.pet_name)} · #TC${p.pet_id}</h4><dl class="grid grid-cols-2 gap-3">${item('Loài', p.pet_type === 'CHO' ? 'Chó' : p.pet_type === 'MEO' ? 'Mèo' : p.pet_type)}${item('Giống', p.breed)}${item('Tuổi', p.age == null ? null : `${p.age} tuổi`)}${item('Cân nặng', `${p.weight} kg`)}<div class="col-span-2">${item('Tiền sử / ghi chú', p.medical_history)}</div></dl></section>`).join('');
        document.getElementById('petDetailsContent').innerHTML = `<section class="border rounded-lg p-3"><h4 class="font-bold text-slate-800 mb-2">Chủ nuôi · #${owner.owner_id}</h4><dl class="grid grid-cols-2 gap-3">${item('Họ tên', owner.full_name)}${contacts}</dl></section><h4 class="font-bold">${selectedPetId === null ? 'Thú cưng của chủ nuôi' : 'Thông tin thú cưng'}</h4>${petCards || '<p class="text-slate-500">Chưa có thú cưng.</p>'}`;
        openModal('modalPetDetails');
    } catch (err) { showToast(err.message, true); }
}
