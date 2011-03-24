/* @type {int} Total number of entries display on page, used for query offset */
var ENTRY_TOTAL = 0

/* @type {Date|null} oldest entry retrieved */
var ENTRY_LATEST = null

/* @type {Picker.Date|null} UI date picker */
var DATEPICKER = null

/* @type {Array} list of fields to get for web UI */
var FIELDS = ['_id', '_date', '_user', 'summary']

/**
 * Convert date in utc
 */
Date.implement({
  // Convert and return date in utc
  utc: function() {
    var localTime = this.getTime()
      , localOffset = this.getTimezoneOffset() * 60000
      , utcTime = localTime + localOffset
    return new Date(utcTime)
  },
  // Format and convert Date for oplog
  oplog: function() {
    return this.utc().format('%Y-%m-%dT%H:%M:%SZ')
  }
})

/**
 * Clear status message
 */
function clearStatus() {
  $('message').set('style', 'display:none')
}

/**
 * Clear datetime picker
 */
function clearDatetime() {
  $('entry-datetime').set('value', '')
  DATEPICKER.date = null
}

function clearEntry() {
  clearStatus()
  clearDatetime()
  $('entry-id').set('value', '')
  $('entry-input').set('value', '')
}

/**
 * Display status message
 *
 * @param {string} text Text message to display
 * @param {string} type Type of message (error, notice, info, success)
 */
function setStatus(text, type) {
  $('message-content').set('text', text)
  $('message').set({'class': type, 'style': 'display:block'})
}
function setError(text) { setStatus(text, 'error') }
function setNotice(text) { setStatus(text, 'notice') }
function setInfo(text) { setStatus(text, 'info') }
function setSuccess(text) { setStatus(text, 'success') }

var INVALID_RESPONSE = { message: 'Invalid response' }

/**
 * Parse rpc response
 *
 * @param {string} method JSON response from rpc function
 * @param {function} fn Callback function
 */
function rpcParse(data, fn) {
  if (typeof data != 'object' || (typeof data.error != 'object' && !data.result)) {
    fn(INVALID_RESPONSE)
  } else if (data.error) {
    if (!data.error.message) return fn(INVALID_RESPONSE)
    fn(data.error)
  } else if (data.result) {
    fn(null, data.result)
  } else {
    fn(INVALID_RESPONSE)
  }
}

/**
 * Execute rpc call
 *
 * @param {string} method Remote method to call
 * @param {Object} params Parameters to send to remote method
 * @param {function} fn Callback function
 */
function rpc(method, params, fn) {
  var request = new Request.JSON({
    url: '/api',
    method: 'post',
    contentTypeString: 'application/json',
    data: JSON.encode({method: method, params: params}),
    onSuccess: function(json, text) { rpcParse(json, fn) }
  })
  request.send()
}

/**
 * Delete log entry by id
 *
 * @param {string} id Entry to id
 * @param {function} fn Callback function
 */
function entryDel(id, fn) {
  if (!id) {
    fn('ID required')
  } else {
    rpc('entry.del', {'_id': id}, function(err) {
      fn(err ? err : null)
    })
  }
}

/**
 * Query and return log entries
 *
 * @param {Object} options Get options
 * @param {function} fn Callback function
 */
function entryGet(values, fn) {
  if (!values.find) {
    fn('Find required')
  } else {
    rpc('entry.get', values, fn)
  }
}

/**
 * Put new log entry
 *
 * @param {Object} values Entry to insert into entry collection
 * @param {function} fn Callback function
 */
function entryPut(entry, fn) {
  rpc('entry.put', entry, function(err, id) {
    if (err) {
      fn(err)
    } else {
      entry._id = id
      fn(null, entry)
    }
  })
}

/**
 * Get entry list
 *
 * @param {?Object} Optional parameters (more, latest)
 */
function uiPopulateEntries(options) {
  options = options || {}

  var entryList = $('entry-list')

  var skip = options.more ? ENTRY_TOTAL : 0
  var find = {}

  if (options.latest && ENTRY_LATEST) {
    find._date = {$gt: ENTRY_LATEST.oplog()}
  } else {
    find._date = {$lt: new Date().oplog()}
  }

  entryGet({ find: find, skip: skip, sort: [['_date', -1]] }, function(err, results) {
    if (err) return setError(err.message || 'Unable to populate entries.')

    if (!options.more && !options.latest) {
      ENTRY_TOTAL = 0
      entryList.empty()
      ENTRY_LATEST = null
    }

    results.each(function(entry, i) {
      var date = new Date(Date.parse(entry._date))

      if (date && (!ENTRY_LATEST || date > ENTRY_LATEST)) {
        ENTRY_LATEST = date
      }
      entryList.grab(uiCreateEntry(entry))
    })
  })
}

/**
 * Create and return entry element
 *
 * @param {Object} entry Single entry
 * @param {function} fn Callback
 */
function uiCreateEntry(entry, fn) {
  ENTRY_TOTAL++

  var date = new Date(Date.parse(entry._date))
  var now = new Date()
  var user = Cookie.read('user')

  // Get time delta in seconds
  var delta = date.diff(now, 'second')

  if (delta <= 60) {
    displayDateTime = 'less than a minute ago'
  } else if (delta > 60 && delta < 3600) {
    // 3 minutes ago
    displayDateTime = parseInt((delta / 60)) + ' minutes ago'
  } else if (delta >= 3600 && delta < 86400 && date.getDate() == now.getDate()) {
    // 18:33:31
    displayDateTime = date.format('%I:%M %p')
  } else {
    if (date.getYear() == now.getYear()) {
      // Jan 27 at 18:33:31
      displayDateTime = date.format('%b %d ') + date.format('at %I:%M %p')
    } else {
      // Jan 27 2011 at 18:33:31
      displayDateTime = date.format('%b %d %Y ') + date.format('at %I:%M %p')
    }
  }

  // Entry row
  var entryDiv = new Element('div', {'class': 'entry', 'id': entry._id})

  // Entry text
  var summaryDiv = new Element('div', {'text': entry.summary})

  // Entry meta fields
  var metaDiv = new Element('div', {'class': 'meta'})
  metaDiv.grab(new Element('div', {'text': displayDateTime}))

  if (entry._user) {
    var controlDiv = new Element('div')

    // If owner add modify links
    if (user && entry._user && user == entry._user) {
      var editLink = new Element('a', {'class': 'entry-edit', 'text': 'edit', 'href': '#/edit/' + entry._id})

      editLink.addEvent('click', function(e) {
        e.stop()

        // Get entry element id that corresponds to _id in MongoDB
        uiEditEntry($(this).getParent().getParent().getParent().get('id'))
        $('entry-input').select()

        return false
      })

      controlDiv.grab(editLink)
      controlDiv.appendText(' - ')

      var deleteLink = new Element('a', {'class': 'entry-delete', 'text': 'delete', 'href': '#/delete/' + entry._id})

      deleteLink.addEvent('click', function(e) {
        e.stop()

        // Get entry element id that corresponds to _id in MongoDB
        uiDeleteEntry($(this).getParent().getParent().getParent().get('id'))
        $('entry-input').select()

        return false
      })

      controlDiv.grab(deleteLink)
      controlDiv.appendText(' - ')
    }

    var userSpan = new Element('span', {'text': entry._user})
    controlDiv.grab(userSpan)

    metaDiv.grab(controlDiv)
  }

  entryDiv.grab(metaDiv)
  entryDiv.grab(summaryDiv)
  entryDiv.grab(new Element('div', {'class': 'clear'}))

  return entryDiv
}

/**
 * Delete entry element
 *
 * @param {string} id Entry id
 * @param {function} fn Callback
 */
function uiDeleteEntry(id, fn) {
  if (confirm('Delete entry?')) {
    entryDel(id, function(err) {
      if (err) return setError(err.message || 'Unable to delete entry.')
      $(id).dispose()
    })
  }
}

/**
 * Edit entry element
 *
 * @param {string} id Entry id
 * @param {function} fn Callback
 */
function uiEditEntry(id, fn) {
  var find = {'_id': id}

  entryGet({find: find, fields: FIELDS}, function(err, results) {
    if (err || !results || !results[0]) return setError('Unable to get entry.')

    var entry = results[0] || {}

    $('entry-input').set('value', entry.summary || '')
    $('entry-id').set('value', id)
    if (entry._date) {
      var date = new Date(Date.parse(entry._date))

      // FIXME(ssewell): doesn't work unless box has already been clicked once
      DATEPICKER.select(date)
    }
  })
}

/**
 * onLoad event for root page
 */
function uiOnLoad() {
  uiPopulateEntries()

  var datetimePicker = $('entry-datetime')
  DATEPICKER = new Picker.Date(datetimePicker, {
    allowEmpty: true,
    pickerClass: 'datepicker_vista',
    timePicker: true,
    positionOffset: {x: -15, y: -30},
    format: '%b %d at %I:%M %p'
  })

  // NOTE(ssewell): ensure we start with a blank date
  clearDatetime()

  // NOTE(ssewell): hack to get DATEPICKER.select work if picker hasn't been
  // opened
  DATEPICKER.opened = true; datetimePicker.focus(); DATEPICKER.opened = false

  // Reset focus to input box
  $('entry-input').focus()

  // Handle form submit
  $('entry-form').addEvent('submit', function(e) {
    e.stop()

    var id = $('entry-id').get('value')
    var entry = {summary: $('entry-input').get('value')}

    if (!entry.summary) {
      return setError('Summary is required.')
    }

    if (DATEPICKER.date && DATEPICKER.date.oplog()) {
      entry._date = DATEPICKER.date.oplog()
    }

    // NOTE(ssewell): future dates are legal, we're just not allowing them from
    // the web gui
    if (entry._date && entry._date > new Date().oplog()) {
      return setError('Date is in the future.')
    }

    if (id) {
      entry = {$set: entry}
      entry._id = id
    } else {
      entry._type = 'user'
    }

    entryPut(entry, function(err) {
      if (err) {
        setError(err.message || 'Unable to put entries.')
      } else {
        clearEntry()
        if (id) {
          // NOTE(ssewell): lazy work around for re-ordering/updating in place
          uiPopulateEntries()
        } else {
          entry._date = entry._date || new Date()
          entry._user = Cookie.read('user')
          $('entry-list').grab(uiCreateEntry(entry), 'top')
        }
      }
    })
  })

  // Handle more link
  $('entry-more').addEvent('click', function(e) {
    e.stop()

    uiPopulateEntries({more: true})

    return false
  })

  // Handle refresh link
  $('entry-refresh').addEvent('click', function(e) {
    e.stop()

    uiPopulateEntries()
    $('entry-input').select()

    return false
  })

  // Handle clear link
  $('entry-clear').addEvent('click', function(e) {
    e.stop()

    clearEntry()
    $('entry-input').select()

    return false
  })
}
