async function refresh(token) {
    const data = await $.ajax({
        url: "/admin/live",
        type: "get",
        dataType: "json",
        error: function (error) {
            return error;
        },
        success: async function (data) {
            return data;
        }
    });
    console.log(data);
    const annotators = data.annotators;
    const counts = data.counts;
    const item_counts = data.item_counts;
    const flag_count = data.flag_count;
    const flags = data.flags;
    const item_count = data.item_count;
    const items = data.items;
    const setting_closed = data.setting_closed;
    const skipped = data.skipped;
    const votes = data.votes;
    const viewed = data.viewed;


    // Populate reports
    let reports_table = document.getElementById("reports-body");
    reports_table.innerHTML = "";
    for (let i = 0; i < flags.length; i++) {
        const flag = flags[i];
        const annotator = await annotators[flag.annotator_id];
        const project = await items[flag.project_id];

        if (!flag.id)
            continue;
        const resolved = flag.resolved ? "open" : "resolve";
        const resolved2 = flag.resolved ? "negative" : "positive";
        const resolved3 = flag.resolved ? "open" : "resolve";

        const reports_template = '<tr class="' + resolved + '">\n' +
            '              <td><span class="admin-check"></span></td>\n' +
            '              <td>' + flag.id + '</td>\n' +
            '              <td>' + annotator.name + '</td>\n' +
            '              <td>' + project.name + '</td>\n' +
            '              <td>' + project.location + '</td>\n' +
            '              <td>' + flag.reason + '</td>\n' +
            '              <td class="compact" data-sort="{{ not flag.resolved }}">\n' +
            '                <form action="/admin/report" method="post">\n' +
            '                  <input type="submit" name="action" value="' + resolved3 + '"\n' +
            '                         class="' + resolved2 + '">\n' +
            '                  <input type="hidden" name="flag_id" value="' + flag.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '            </tr>';


        const newRow = reports_table.insertRow(reports_table.rows.length);
        newRow.innerHTML = reports_template;

    }

    /*<tr class="{{ 'disabled' if not item.active else 'prioritized' if item.prioritized else ''}}">
              <td><span class="admin-check"></span></td>
              <td><a href="{{ url_for('item_detail', item_id=item.id) }}" class="colored">{{ item.id }}</a></td>
              <td>{{ item.name | safe }}</td>
              <td>{{ item.location | safe }}</td>
              <td class="preserve-formatting">{{ item.description | safe }}</td>
              <td>{{ item.mu | round(4) }}</td>
              <td>{{ item.sigma_sq | round(4) }}</td>
              <td>{{ item_counts.get(item.id, 0) }}</td>
              <td>{{ item.viewed | length }}</td>
              <td>{{ skipped.get(item.id, 0) }}</td>
              <td class="compact" data-sort="{{ item.prioritized }}">
                <form action="/admin/item" method="post">
                  <input type="submit" name="action" value="{{ 'Prioritize' if not item.prioritized else 'Cancel' }}"
                         class="{{ 'positive' if not item.prioritized else 'negative' }}">
                  <input type="hidden" name="item_id" value="{{ item.id }}">
                  <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                </form>
              </td>
              <td class="compact" data-sort="{{ item.active }}">
                <form action="/admin/item" method="post">
                  <input type="submit" name="action" value="{{ 'Disable' if item.active else 'Enable' }}"
                         class="{{ 'negative' if item.active else 'positive' }}">
                  <input type="hidden" name="item_id" value="{{ item.id }}">
                  <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                </form>
              </td>
              <td class="compact">
                <form action="/admin/item" method="post">
                  <input type="submit" name="action" value="Delete" class="negative">
                  <input type="hidden" name="item_id" value="{{ item.id }}">
                  <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                </form>
              </td>
            </tr>*/

    // Populate projects
    let projects_table = document.getElementById("items-body");
    projects_table.innerHTML = "";
    for (let i = 0; i < items.length; i++) {
        const item = items[i];

        if (!item.id)
            continue;


        const items_template = '<tr class="' + (item.active ? item.prioritized ? 'prioritized' : '' : 'disabled') + '">\n' +
            '              <td><span class="admin-check"></span></td>\n' +
            '              <td><a href="{{ url_for(\'item_detail\', item_id=' + item.id + ') }}" class="colored">' + item.id + '</a></td>\n' +
            '              <td>' + item.name + '</td>\n' +
            '              <td>' + item.location + '</td>\n' +
            '              <td class="preserve-formatting">' + item.description + '</td>\n' +
            '              <td>' + item.mu.toFixed(4) + '</td>\n' +
            '              <td>' + item.sigma_sq.toFixed(4) + '</td>\n' +
            '              <td>' + item_counts[item.id] + '</td>\n' +
            '              <td>' + viewed[item.id] + '</td>\n' +
            '              <td>' + skipped[item.id] + '</td>\n' +
            '              <td class="compact" data-sort="' + item.prioritized + '">\n' +
            '                <form action="/admin/item" method="post">\n' +
            '                  <input type="submit" name="action" value="' + (item.prioritized ? 'Cancel' : 'Prioritize') + '"\n' +
            '                         class="' + (item.prioritized ? 'negative' : 'positive') + '">\n' +
            '                  <input type="hidden" name="item_id" value="' + item.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '              <td class="compact" data-sort="' + item.active + '">\n' +
            '                <form action="/admin/item" method="post">\n' +
            '                  <input type="submit" name="action" value="' + (item.active ? 'Disable' : 'Enable') + '"\n' +
            '                         class="' + (item.active ? 'negative' : 'positive') + '">\n' +
            '                  <input type="hidden" name="item_id" value="' + item.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '              <td class="compact">\n' +
            '                <form action="/admin/item" method="post">\n' +
            '                  <input type="submit" name="action" value="Delete" class="negative">\n' +
            '                  <input type="hidden" name="item_id" value="' + item.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '            </tr>';


        //TODO: Can use item.placement object
        const newRow = projects_table.insertRow(projects_table.rows.length);
        newRow.innerHTML = items_template;

    }

    $('#judges').trigger("update");
    $('#reports').trigger("update");
    $('#projects').trigger("update");
}
