<?xml version="1.0" encoding="utf-8"?>
<!--
	# Transformation include for fault text XML to HTML.
!-->
<xsl:transform version="1.0"
	xmlns="http://www.w3.org/1999/xhtml"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xlink="http://www.w3.org/1999/xlink"
	xmlns:set="http://exslt.org/sets"
	xmlns:str="http://exslt.org/strings"
	xmlns:exsl="http://exslt.org/common"
	xmlns:txt="http://if.fault.io/xml/text"
	xmlns:func="http://exslt.org/functions"
	extension-element-prefixes="func"
	exclude-result-prefixes="set str exsl func xl xsl txt">

	<xsl:template match="txt:emphasis[@weight=1]">
		<span class="text.emphasis"><xsl:value-of select="text()"/></span>
	</xsl:template>

	<xsl:template match="txt:emphasis[@weight=2]">
		<span class="text.emphasis.heavy"><xsl:value-of select="text()"/></span>
	</xsl:template>

	<xsl:template match="txt:emphasis[@weight>2]">
		<span class="text.emphasis.excessive"><xsl:value-of select="text()"/></span>
	</xsl:template>

	<xsl:template match="txt:literal">
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

	<xsl:template match="txt:literals">
		<xsl:variable name="start" select="txt:line[text()][1]"/>
		<xsl:variable name="stop" select="txt:line[text()][last()]"/>
		<xsl:variable name="lang" select="substring-after(@type, '/pl/')"/>
		<xsl:variable name="is.text" select="@type = 'text'"/>

		<!--
			# The source XML may contain leading and trailing empty lines
			# the selection filters empty txt:line's on the edges
		!-->
		<div class="text.literals">
			<pre>
					<xsl:attribute name="class">
						<xsl:choose>
							<xsl:when test="$is.text">
								<xsl:value-of select="raw.text"/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:value-of select="concat('language-', $lang)"/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:attribute>
					<xsl:for-each
						select="txt:line[.=$start or .=$stop or (preceding-sibling::txt:*[.=$start] and following-sibling::txt:*[.=$stop])]">
						<xsl:value-of select="concat(text(), '&#10;')"/>
					</xsl:for-each>
			</pre>
		</div>
	</xsl:template>

	<xsl:template match="txt:dictionary">
		<dl class="text">
			<xsl:for-each select="txt:item">
				<dt><xsl:apply-templates select="txt:key/txt:*|txt:key/text()"/></dt>
				<dd><xsl:apply-templates select="txt:value/txt:*"/></dd>
			</xsl:for-each>
		</dl>
	</xsl:template>

	<xsl:template match="txt:sequence">
		<ol class="text">
			<xsl:for-each select="txt:item">
				<li><xsl:apply-templates select="txt:*|text()"/></li>
			</xsl:for-each>
		</ol>
	</xsl:template>

	<xsl:template match="txt:set">
		<ul class="text">
			<xsl:for-each select="txt:item">
				<li><xsl:apply-templates select="txt:*|text()"/></li>
			</xsl:for-each>
		</ul>
	</xsl:template>

	<xsl:template match="txt:paragraph">
		<p><xsl:apply-templates select="node()"/></p>
	</xsl:template>

	<xsl:template match="txt:reference">
		<a class="text.reference" href="{@href}"><xsl:value-of select="@source"/><span class="ern"/></a>
	</xsl:template>

	<xsl:template match="txt:section[not(@title)]">
		<xsl:variable name="address" select="concat(((ancestor::*[@xml:id][1]/@xml:id)|exsl:node-set('@'))[1], ':header:')"/>

		<!-- Don't include the div if the leading section is empty -->
		<xsl:if test="txt:*">
			<div id="{translate($address, ' ', '-')}"><xsl:apply-templates select="txt:*"/></div>
		</xsl:if>
	</xsl:template>

	<xsl:template match="txt:section[@title]">
		<!-- if there is no identified ancestor, it's probably the root object (module) -->
		<xsl:variable name="address"
			select="concat(((ancestor::*[@xml:id and local-name()!='module'][1]/@xml:id))[1], '::', @title)"/>
		<xsl:variable name="id" select="translate($address, ' ', '-')"/>

		<section id="{$id}"
			class="fault.text"><a href="{concat('#', $id)}"><div class="section.title"><xsl:value-of
					select="@title"/></div></a><xsl:apply-templates select="txt:*"/></section>
	</xsl:template>
</xsl:transform>
