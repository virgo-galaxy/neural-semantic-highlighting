def describe_payload(payload)
  case payload
  in { title:, views: Integer => count } if count.positive?
    "#{title}: #{count} views"
  in { title: }
    "#{title}: no views yet"
  in [first, *remaining]
    "First #{first}, remaining #{remaining.size}"
  else
    "Unknown payload"
  end
end

def extract_title(payload)
  payload => { title: }
  title
rescue NoMatchingPatternError => problem
  warn problem.message
  nil
end
