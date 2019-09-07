const N = "Null";
function openProjectModal(item, token) {
  const itemModal = `
    <div class="info" style="padding: 0;">
      <style>
        th {
          text-align: left;
        }
    
        p {
          line-height: 0;
          margin: 0;
        }
      </style>
      <h4 class="normal-20" id="title">Project ID: <span id="id">{{ item.id }}</span></h4>
      <p class="normal-14"><span class="bold-14">Name: </span>
      <span>
        <form action="/admin/item_patch" method="post" class="form-inline">
          <input type="text" name="name" value="${ item.name || N }">
          <button type="submit" name="action" value="Update" >Update</button>
          <input type="hidden" name="item_id" value="${ item.id }">
          <input type="hidden" name="_csrf_token" value="${ token }">
        </form>
      </span>
      </p>
      <p class="normal-14"><span class="bold-14">Location: </span>
        <span>
          <form action="/admin/item_patch" method="post" class="form-inline">
            <input type="text" name="location" value="${ item.location || N }">
            <button type="submit" name="action" value="Update">Update</button>
            <input type="hidden" name="item_id" value="${ item.id }">
            <input type="hidden" name="_csrf_token" value="${ token }">
          </form>
        </span>
      </p>
      <p class="normal-14">
        <span class="bold-14">Description:</span>
        <br>
        <span>
          <textarea name="description" form="description_form">${ item.description | N }</textarea>
          <form action="/admin/item_patch" method="post" id="description_form" class="form-inline">
            <input type="hidden" name="item_id" value="${ item.id }">
            <input type="hidden" name="_csrf_token" value="${ token }">
            <button type="submit" name="action" value="Update">Update</button>
          </form>
        </span>
      </p>
      <p class="normal-14"><span class="bold-14">Mu: </span>${ item.mu }</p>
      <p class="normal-14"><span class="bold-14">Sigma Squared: </span${ item.sigma_sq }</p>
      <p class="normal-14"><span class="bold-14">Seen By Judges: </span>
      <span>
      ${(item.viewed.map((annotator) => {
        return "<span><a href=\"{{ url_for('annotator_detail', annotator_id=annotator.id) }}\" class=\"colored\">${ annotator.id }},</a></span>"
       }))}
        {% for annotator in item.viewed %}
                  <span><a href="{{ url_for('annotator_detail', annotator_id=annotator.id) }}"
                         class="colored">{{ annotator.id }},</a></span>
                {% endfor %}
      </span>
      </p>
      <p class="normal-14"><span class="bold-14">Skipped By Judges: </span>
      <span>
        {% for annotator in skipped %}
                  <span><a href="{{ url_for('annotator_detail', annotator_id=annotator.id) }}"
                         class="colored">{{ annotator.id }},</a></span>
                {% endfor %}
      </span>
      </p>
    </div>
  `;
}
