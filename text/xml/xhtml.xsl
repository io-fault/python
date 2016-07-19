<?xml version="1.0" encoding="utf-8"?>
<!--
 ! Transformation include for fault text XML to HTML.
 !-->
<xsl:transform version="1.0"
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:xl="http://www.w3.org/1999/xlink"
 xmlns:set="http://exslt.org/sets"
 xmlns:str="http://exslt.org/strings"
 xmlns:exsl="http://exslt.org/common"
 xmlns:e="https://fault.io/xml/text"
 xmlns:func="http://exslt.org/functions"
 extension-element-prefixes="func"
 exclude-result-prefixes="set str exsl func xl xsl doc py e">

 <xsl:template match="e:emphasis[@weight=1]">
  <span class="eclectic.emphasis"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template match="e:emphasis[@weight=2]">
  <span class="eclectic.emphasis.heavy"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template match="e:emphasis[@weight>2]">
  <span class="eclectic.emphasis.excessive"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template match="e:literal">
  <!-- inline literal -->
  <xsl:choose>
   <xsl:when test="not(@cast)">
    <code class="language-python"><xsl:value-of select="text()"/></code>
   </xsl:when>
   <xsl:otherwise>
    <span class="{concat('cast-', @cast)}"><xsl:value-of select="text()"/></span>
   </xsl:otherwise>
  </xsl:choose>
 </xsl:template>

 <xsl:template match="e:literals">
  <xsl:variable name="start" select="e:line[text()][1]"/>
  <xsl:variable name="stop" select="e:line[text()][last()]"/>
  <xsl:variable name="lang" select="substring-after(@type, '/pl/')"/>
  <xsl:variable name="is.text" select="@type = 'text'"/>

  <!-- the source XML may contain leading and trailing empty lines -->
  <!-- the selection filters empty e:line's on the edges -->
  <div class="eclectic.literals">
   <pre>
     <xsl:attribute name="class">
      <xsl:choose>
       <xsl:when test="$is.text">
        <xsl:value-of select="raw.text">
       </xsl:when>
       <xsl:otherwise>
		  <xsl:value-of select="concat('language-', $lang)"/>
       </xsl:otherwise>
      </xsl:choose>
     </xsl:attribute>
     <xsl:for-each
      select="e:line[.=$start or .=$stop or (preceding-sibling::e:*[.=$start] and following-sibling::e:*[.=$stop])]">
      <xsl:value-of select="concat(text(), '&#10;')"/>
     </xsl:for-each>
   </pre>
  </div>
 </xsl:template>

 <xsl:template match="e:dictionary">
  <dl class="eclectic">
   <xsl:for-each select="e:item">
    <dt><xsl:apply-templates select="e:key/e:*|e:key/text()"/></dt>
    <dd><xsl:apply-templates select="e:value/e:*"/></dd>
   </xsl:for-each>
  </dl>
 </xsl:template>

 <xsl:template match="e:sequence">
  <ol class="eclectic">
   <xsl:for-each select="e:item">
    <li><xsl:apply-templates select="e:*|text()"/></li>
   </xsl:for-each>
  </ol>
 </xsl:template>

 <xsl:template match="e:set">
  <ul class="eclectic">
   <xsl:for-each select="e:item">
    <li><xsl:apply-templates select="e:*|text()"/></li>
   </xsl:for-each>
  </ul>
 </xsl:template>

 <xsl:template match="e:paragraph">
  <p><xsl:apply-templates select="node()"/></p>
 </xsl:template>

 <xsl:template match="e:reference">
  <a class="eclectic.reference" href="{@href}"><xsl:value-of select="@source"/><span class="ern"/></a>
 </xsl:template>

 <xsl:template match="e:section[not(@title)]">
  <xsl:variable name="address" select="concat(((ancestor::*[@xml:id][1]/@xml:id)|exsl:node-set('@'))[1], ':header:')"/>

  <!-- Don't include the div if the leading section is empty -->
  <xsl:if test="e:*">
   <div id="{translate($address, ' ', '-')}"><xsl:apply-templates select="e:*"/></div>
  </xsl:if>
 </xsl:template>

 <xsl:template match="e:section[@title]">
  <!-- if there is no identified ancestor, it's probably the root object (module) -->
  <xsl:variable name="address"
   select="concat(((ancestor::*[@xml:id and local-name()!='module'][1]/@xml:id))[1], '::', @title)"/>
  <xsl:variable name="id" select="translate($address, ' ', '-')"/>

  <div id="{$id}"
   class="section"><a href="{concat('#', $id)}"><div class="section.title"><xsl:value-of
     select="@title"/></div></a><xsl:apply-templates select="e:*"/></div>
 </xsl:template>
</xsl:transform>
