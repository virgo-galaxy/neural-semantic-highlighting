def ranked_titles(documents, minimum_views: 20)
  documents
    .select { |document| document[:published] }
    .select { |document| document[:views] >= minimum_views }
    .sort_by { |document| -document[:views] }
    .map { |document| document[:title].strip }
end

counts = { open: 4, done: 8, draft: nil }
labels = counts.compact.map do |status, count|
  "#{status}: #{count}"
end

lengths = labels.map { _1.length }
puts lengths.sum
