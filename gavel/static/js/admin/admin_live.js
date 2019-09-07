let currentAnnotators;
let currentItems;

/*
* BEGIN REFRESH FUNCTION
* */
async function refresh(token) {
    const data = await $.ajax({
        url: "/admin/live",
        type: "get",
        dataType: "json",
        error: function (error) {
            return error;
        },
        success: async function (data) {
            await data;
        }
    });

    const now = new Date();

    const annotators = data.annotators;
    const counts = data.counts;
    const item_counts = data.item_counts;
    const flag_count = data.flag_count;
    const flags = data.flags;
    const item_count = data.item_count;
    const items = data.items;
    const setting_closed = data.setting_closed;
    const setting_stop_queue = data.setting_stop_queue;
    const skipped = data.skipped;
    const votes = data.votes;
    const viewed = data.viewed;
    const sigma = data.average_sigma;
    const seen = data.average_seen;

    // Populate vote count
    let vote_count = document.getElementById("total-votes");
    vote_count.innerText = votes;

    // Populate total active projects
    let total_active = document.getElementById("total-active");
    total_active.innerText = item_count;

    // Populate avg. sigma^2
    let average_sigma = document.getElementById("average-sigma");
    average_sigma.innerText = sigma.toFixed(4);

    let average_seen = document.getElementById("average-seen");
    average_seen.innerText = seen.toFixed(2);

    // Populate reports
    let reports_table = document.getElementById("reports-body");
    reports_table.innerHTML = "";

    for (let i = 0; i < flags.length; i++) {

        try {
            const flag = flags[i];

            if (!flag.id)
                continue;

            const reports_template = `
            <tr class="${flag.resolved ? "open" : "resolve"}">
              <td><input id="${flag.id}" type="checkbox" name="item" value="${flag.item.id}" class="admin-check"/></td>
              <td>${flag.id}</td>
              <td><a onclick="openJudge(${flag.annotator.id})" href="#" class="colored">${flag.annotator.name}</a></td>
              <td><a onclick="openProject(${flag.item.id})" href="#" class="colored">${flag.item.name}</a></td>
              <td>${flag.item.location}</td>
              <td>${flag.reason}</td>
              <td>
                <form action="/admin/report" method="post" class="inline-block">
                  <button type="submit" class="button-full background-purple h-32 text-12 text-bold uppercase">Resolve Flag</button>
                  <input type="hidden" name="action" value="${flag.resolved ? "open" : "resolve"}"
                         class="${flag.resolved ? "negative" : "positive"}">
                  <input type="hidden" name="flag_id" value="${flag.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
            </tr>`;


            const newRow = reports_table.insertRow(reports_table.rows.length);
            newRow.innerHTML = reports_template;


        } catch (e) {
            console.log(e);
        }

    }

    // Populate projects
    let projects_table = document.getElementById("items-body");
    projects_table.innerHTML = "";
    currentItems = items;
    for (let i = 0; i < items.length; i++) {
        try {
            const item = items[i];

            if (!item.id)
                continue;

            // language=HTML
            const items_template = `
            <tr class="${(item.active ? item.prioritized ? 'prioritized' : '' : 'disabled')}">
              <td id="project-check-container"><input id="${item.id}" type="checkbox" name="item" value="${item.id}" class="admin-check"/></td>
              <td><a onclick="openProject(${item.id})" class="colored">${item.id}</a></td>
              <td>${item.name}</td>
              <td>${item.location}</td>
              <td class="preserve-formatting">${item.description}</td>
              <td>${item.mu.toFixed(4)}</td>
              <td>${item.sigma_sq.toFixed(4)}</td>
              <td>${item_counts[item.id]}</td>
              <td>${item.viewed.length}</td>
              <td>${skipped[item.id]}</td>
              <td data-sort="${item.prioritized}">
                <span onclick="openProject(${item.id})" class="inline-block tooltip">
                  <button class="nobackgroundnoborder">
                    <i class="fas fa-pencil-alt"></i>
                  </button>
                  <span class="tooltiptext">Edit Project</span>
                </span>
                <form action="/admin/item" method="post" class="inline-block tooltip">
                  <button type="submit" class="nobackgroundnoborder"><i class="fas ${(item.prioritized ? 'fa-chevron-down' : 'fa-chevron-up')}"></i></button>
                  <span class="tooltiptext">${(item.prioritized ? 'Cancel' : 'Prioritize')}</span>
                  <input type="hidden" name="action" value="${(item.prioritized ? 'Cancel' : 'Prioritize')}"
                         class="${(item.prioritized ? 'negative' : 'positive')}">
                  <input type="hidden" name="item_id" value="${item.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
                <form action="/admin/item" method="post" class="inline-block tooltip">
                  <button type="submit" class="nobackgroundnoborder"><i class="fas ${(item.active ? 'fa-eye' : 'fa-eye-slash')}"></i></button>
                  <span class="tooltiptext">${(item.active ? 'Deactivate' : 'Activate')}</span>
                  <input type="hidden" name="action" value="${(item.active ? 'Disable' : 'Enable')}"
                         class="${(item.active ? 'negative' : 'positive')}">
                  <input type="hidden" name="item_id" value="${item.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
                <form action="/admin/item" method="post" class="inline-block tooltip">
                  <button type="submit" class="nobackgroundnoborder"><i class="fas fa-trash-alt"></i></button>
                  <span class="tooltiptext">Delete</span>
                  <input type="hidden" name="action" value="Delete" class="negative">
                  <input type="hidden" name="item_id" value="${item.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
            </tr>`;

            const newRow = projects_table.insertRow(projects_table.rows.length);
            newRow.innerHTML = items_template;
        } catch (e) {
            console.log(e)
        }

    }

    // Populate Judges
    let judges_table = document.getElementById("judges-body");
    judges_table.innerHTML = "";
    currentAnnotators = annotators;

    for (let i = 0; i < annotators.length; i++) {
        try {
            const annotator = annotators[i];

            if (!annotator.id)
                continue;

            // language=HTML
            const annotator_template = `
            <tr class=${annotator.active ? '' : 'disabled'}>
              <td id="judge-check-container"><input id="${annotator.id}" type="checkbox" name="annotator" value="${annotator.id}" class="admin-check"/></td>
              <td><a onclick="openJudge(${annotator.id})" class="colored">${annotator.id}</a></td>
              <td>${annotator.name}</td>
              <td>${annotator.email}</td>
              <td class="preserve-formatting">${annotator.description}</td>
              <td>${(counts[annotator.id] || 0)}</td>
              <td>${(annotator.next_id || 'None')}</td>
              <td>${(annotator.prev_id || 'None')}</td>
              <td>${(annotator.updated ? (((now - (Date.parse(annotator.updated) - now.getTimezoneOffset()*60*1000))/60)/1000).toFixed(0) + " min ago" : "Undefined")}</td>
              <td data-sort="${annotator.active}">
                <span onclick="openJudge(${annotator.id})" class="inline-block tooltip">
                  <button class="nobackgroundnoborder">
                    <i class="fas fa-pencil-alt"></i>
                  </button>
                  <span class="tooltiptext">Edit Judge</span>
                </span>
                <form action="/admin/annotator" method="post" class="inline-block tooltip">
                  <button type="submit" class="nobackgroundnoborder"><i class="fas fa-envelope"></i></button>
                  <span class="tooltiptext">Send Email</span>
                  <input type="hidden" name="action" value="Email" class="neutral">
                  <input type="hidden" name="annotator_id" value="${annotator.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
                <form action="/admin/annotator" method="post" class="inline-block tooltip">
                  <button type="submit" class="nobackgroundnoborder"><i class="fas ${(annotator.active ? 'fa-eye' : 'fa-eye-slash')}"></i></button>
                  <span class="tooltiptext">${(annotator.active ? 'De-Activate' : 'Activate')}</span>
                  <input type="hidden" name="action" value="${(annotator.active ? 'Disable' : 'Enable')}"
                         class="${(annotator.active ? 'negative' : 'positive')}">
                  <input type="hidden" name="annotator_id" value="${annotator.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
                <form action="/admin/annotator" method="post" class="inline-block tooltip">
                  <button type="submit" class="nobackgroundnoborder"><i class="fas fa-trash-alt"></i></button>
                  <input type="hidden" name="action" value="Delete" class="negative">
                  <span class="tooltiptext">Delete</span>
                  <input type="hidden" name="annotator_id" value="${annotator.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
            </tr>`;

            const newRow = judges_table.insertRow(judges_table.rows.length);
            newRow.innerHTML = annotator_template;
        } catch (e) {
            console.log(e);
        }
    }

    $('#judges').trigger("update");
    $('#reports').trigger("update");
    $('#projects').trigger("update");

    //document.querySelector('.admin-check').checked = localStorage.e.target.checked
}

/*
* END REFRESH FUNCTION
* */

function toggleSelector() {
    const selectorModal = document.getElementById("selector");
    selectorModal.style.display = selectorModal.style.display === "block" ? "none" : "block";
}

function showTab(e) {
    const judges = document.getElementById("admin-judges");
    const projects = document.getElementById("admin-projects");
    const reports = document.getElementById("admin-reports");
    const content = document.getElementById("admin-switcher-content");
    const batch = document.getElementById("batchPanel");
    currentTab = e;
    judges.style.display = "none";
    projects.style.display = "none";
    reports.style.display = "none";
    content.innerText = "none";
    batch.style.display = "none";
    localStorage.setItem("currentTab", e);
    switch (localStorage.getItem("currentTab")) {
        case "judges":
            judges.style.display = "block";
            content.innerText = "Manage Judges";
            batch.style.display = "inline-block";
            break;
        case "projects":
            projects.style.display = "block";
            content.innerText = "Manage Projects";
            batch.style.display = "inline-block";
            break;
        case "reports":
            reports.style.display = "block";
            content.innerText = "Manage Reports";
            break;
        default:
            reports.style.display = "block";
            content.innerText = "Manage Reports";
            break;
    }
    setAddButtonState();
}

window.addEventListener("DOMContentLoaded", function () {
    showTab(localStorage.getItem("currentTab") || "admin-reports");
});

function setAddButtonState() {
    const judges = document.getElementById("admin-judges").style.display === "block";
    const projects = document.getElementById("admin-projects").style.display === "block";
    const reports = document.getElementById("admin-reports").style.display === "block";
    const text = document.getElementById('add-text');
    const add = document.getElementById('add');
    if (!!judges) {
        text.innerText = "+ Add Judges";
        text.onclick = function () {
            openModal('add-judges')
        };
        //text.addEventListener('onclick', openModal('add-judges'));
    }
    if (!!projects) {
        text.innerText = "+ Add Projects";
        text.onclick = function () {
            openModal('add-projects')
        };
        //text.addEventListener('onclick', openModal('add-projects'));
    }
    if (!!reports) {
        text.innerText = "";
        text.onclick = null;
    }
}

function openModal(modal) {
    $("body").find(".modal-wrapper").css('display', 'none');

    var dumdum;
    modal !== 'close' && modal ? document.getElementById(modal).style.display = 'block' : dumdum = 'dum';
}

$(".full-modal").click(function (event) {
    //if you click on anything except the modal itself or the "open modal" link, close the modal
    if (!$(event.target).hasClass('admin-modal-content') && $(event.target).hasClass('full-modal')) {
        openModal('close')
    }
    if (!$(event.target).hasClass('admin-switcher-modal') &&
        !$(event.target).parents('*').hasClass('admin-switcher') &&
        !$(event.target).hasClass('admin-switcher')) {
        $("body").find("#selector").css('display', 'none')
    }
});

function checkAllReports() {
    let check = document.getElementById('check-all-reports');
    if (check.checked) {
        $('#reports').find('input[type=checkbox]').each(function () {
            this.checked = true;
        });
        check.checked = true;
    } else {
        $('#reports').find('input[type=checkbox]:checked').each(function () {
            this.checked = false;
        });
        check.checked = false;
    }
}

function checkAllProjects() {
    let check = document.getElementById('check-all-projects');
    if (check.checked) {
        $('#projects').find('input[type=checkbox]').each(function () {
            this.checked = true;
        });
        check.checked = true;
    } else {
        $('#projects').find('input[type=checkbox]:checked').each(function () {
            this.checked = false;
        });
        check.checked = false;
    }
}

function checkAllJudges() {
    let check = document.getElementById('check-all-judges');
    if (check.checked) {
        $('#judges').find('input[type=checkbox]').each(function () {
            this.checked = true;
        });
        check.checked = true;
    } else {
        $('#judges').find('input[type=checkbox]:checked').each(function () {
            this.checked = false;
        });
        check.checked = false;
    }
}

const judgeCheckboxValues = JSON.parse(localStorage.getItem('judgeCheckboxValues')) || {};
const $judgeCheckboxes = $("#judge-check-container :checkbox");
$judgeCheckboxes.on("change", function() {
    $judgeCheckboxes.each(function() {
        judgeCheckboxValues[this.id] = this.checked;
    });
    localStorage.setItem("judgeCheckboxValues", JSON.stringify(judgeCheckboxValues))
});

const projectCheckboxValues = JSON.parse(localStorage.getItem('projectCheckboxValues')) || {};
const $projectCheckboxes = $("#project-check-container :checkbox");
$projectCheckboxes.on("change", function() {
    $projectCheckboxes.each(function() {
        projectCheckboxValues[this.id] = this.checked;
    });
    localStorage.setItem("projectCheckboxValues", JSON.stringify(projectCheckboxValues))
});

let judgeIds = [];
let projectIds = [];
let form = null;
$('#batchDelete').click(async function () {
    projectIds = [];
    judgeIds = [];
    form = null;
    if (currentTab === 'projects') {
        form = document.getElementById('batchDeleteItems');
    } else if (currentTab === 'judges') {
        form = document.getElementById('batchDeleteAnnotators');
    }
    $('#' + currentTab).find('input[type="checkbox"]:checked').each(function () {
        form.innerHTML = form.innerHTML + '<input type="hidden" name="ids" value="' + this.id + '"/>';
    });
    try {
        form.serializeArray()
    } catch {

    }
    const full = await form;
    await full.submit();

});

$('#batchDisable').click(async function () {
    projectIds = [];
    judgeIds = [];
    form = null;
    if (currentTab === 'projects') {
        form = document.getElementById('batchDisableItems');
    } else if (currentTab === 'judges') {
        form = document.getElementById('batchDisableAnnotators');
    }
    $('#' + currentTab).find('input[type="checkbox"]:checked').each(function () {
        form.innerHTML = form.innerHTML + '<input type="hidden" name="ids" value="' + this.id + '"/>';
    });
    try {
        form.serializeArray();
    } catch {

    }
    const full = await form;
    await full.submit();
});
