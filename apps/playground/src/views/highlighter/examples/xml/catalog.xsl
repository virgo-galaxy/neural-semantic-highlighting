<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html"/>
  <xsl:template match="/catalog">
    <ul>
      <xsl:for-each select="book">
        <li><xsl:value-of select="title"/></li>
      </xsl:for-each>
    </ul>
  </xsl:template>
</xsl:stylesheet>
