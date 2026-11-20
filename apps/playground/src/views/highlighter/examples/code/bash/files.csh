#!/bin/tcsh
set files = ( source.c source.h )

foreach file ( $files )
  if ( -f "$file" ) then
    echo "Found $file"
  endif
end
