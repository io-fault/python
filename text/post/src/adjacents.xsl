<?xml version="1.0" encoding="utf-8"?>
<?xml-library symbol="adjacents" type="application/xslt+xml" namespace="xsl"?>
<!--
	# Process fault.xml surrounding paragraph elements with group elements allowing
	# trivial detection of adjacent text that might impact downstream formatting
	# or semantics.
!-->
<xsl:transform version="1.0"
	xmlns="http://if.fault.io/xml/text"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:exsl="http://exslt.org/common"
	xmlns:str="http://exslt.org/strings"
	xmlns:txt="http://if.fault.io/xml/text"
	xmlns:fault="http://fault.io/xml/xpath"
	xmlns:ctl="http://fault.io/xml/control"
	xmlns:xi="http://www.w3.org/2001/XInclude"
	extension-element-prefixes="exsl">

	<!--
		# While this looks of questionable utility, the roff (manpage) downstream
		# has particulars involving punctuation that make formatting semantic
		# markup/macros difficult without having the elements (emphasis, literal, etc) to
		# be mapped along with the surrounding text. Once the prefix and suffix are
		# identified groups with special cases can be easily handled on a case by case basis.

		# adjacents is provided as a fault.text processing module as the utility of this
		# is likely to extend beyond the roff downstream.
	!-->

	<ctl:library symbol="adjacents" type="application/xslt+xml" namespace="xsl"/>
	<ctl:namespaces fault:keep="no" xi:keep="no" exsl:keep="no"/>

	<xsl:output method="xml" encoding="utf-8" indent="no"/>

	<xsl:param name="adjacents.delimiter" select="' '"/>

	<xsl:template name="join">
		<!--
			# Preserving order, iterate over the paragraph content
			# nodes grouping non-whitespace characters adjacent to elements
			# with the elements.
		!-->
		<xsl:variable name="nodes" select="*|text()|processing-instruction()"/>

		<!--
			# ! WARNING: (term)`XML Processing Instructions` might not be handled properly here.
		!-->

		<xsl:variable name="first.node" select="$nodes[position()=1]"/>
		<xsl:variable name="last.node" select="$nodes[position()=last()]"/>

		<xsl:element name="{name(.)}" namespace="{namespace-uri(.)}">
			<xsl:copy-of select="namespace::*"/>
			<xsl:copy-of select="@*"/>

			<xsl:for-each select="$nodes">
				<!--
					# Arguably this implementation is logically and mechanically inefficient.
					# The loop iterates over both text nodes and elements branching into
					# a solution. The issue is that it's performing redundant operations
					# in order to detect the edge of the text that is to be included in the group.
				!-->
				<xsl:variable name="p" select="position()"/>

				<xsl:choose>
					<xsl:when test="self::processing-instruction()">
						<xsl:copy-of select="."/>
					</xsl:when>

					<xsl:when test="self::text() and .!=''">
						<!--
							# Trim the characters adjacent to the edges.
							# Conditions used to choose trim: non-whitespace adjacent text to element node.
						!-->
						<xsl:variable name="txt" select="."/>
						<xsl:variable name="former" select="$nodes[position()=($p - 1)]"/>
						<xsl:variable name="latter" select="$nodes[position()=($p + 1)]"/>
						<xsl:variable name="i.prefix" select="substring($txt, 1, 1)"/>
						<xsl:variable name="i.suffix" select="substring($txt, string-length($txt), 1)"/>
						<xsl:variable name="has.prefix"
							select="boolean($former/self::*) and string-length($i.prefix) > 0 and $i.prefix != $adjacents.delimiter"/>
						<xsl:variable name="has.suffix"
							select="boolean($latter/self::*) and string-length($i.suffix) > 0 and $i.suffix != $adjacents.delimiter"/>

						<xsl:choose>
							<xsl:when test="$has.prefix and $has.suffix">
								<xsl:variable name="init" select="normalize-space(.)"/>
								<xsl:variable name="split" select="str:split($init, $adjacents.delimiter)"/>

								<!--
									# Include leading space if there are fields.
								!-->
								<xsl:if test="count($split/*) > 0">
									<xsl:text> </xsl:text>
								</xsl:if>
								<!--
									# Filter leading and final fields as they're handled by the element.
								!-->
								<xsl:for-each select="$split[position()>1 and last()>position()]">
									<xsl:value-of select="."/>
									<xsl:text> </xsl:text>
								</xsl:for-each>
							</xsl:when>

							<xsl:when test="$has.prefix">
								<!--
									# Trim the adjacent prefix.
								!-->
								<xsl:variable name="fields" select="str:split(normalize-space(.), $adjacents.delimiter)"/>

								<xsl:for-each select="$fields[position()>1]">
									<xsl:text> </xsl:text>
									<xsl:value-of select="."/>
								</xsl:for-each>
							</xsl:when>

							<xsl:when test="$has.suffix">
								<!--
									# Trim the adjacent suffix.
								!-->
								<xsl:variable name="fields" select="str:split(normalize-space(.), $adjacents.delimiter)"/>

								<xsl:for-each select="$fields[last()>position()]">
									<xsl:value-of select="."/>
									<xsl:text> </xsl:text>
								</xsl:for-each>
							</xsl:when>

							<xsl:otherwise>
								<!--
									# No adjacent non-space. Adjacent elements will not pull these in.
								!-->
								<xsl:copy-of select="."/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:when>

					<xsl:otherwise>
						<!--
							# Element. Group adjacent non-whitespace characters if there are any.
						!-->
						<xsl:variable name="former" select="$nodes[position()=($p - 1)]"/>
						<xsl:variable name="former.element" select="$nodes[position()=($p - 2)]"/>
						<xsl:variable name="latter" select="$nodes[position()=($p + 1)]"/>
						<xsl:variable name="latter.element" select="$nodes[position()=($p + 2)]"/>

						<xsl:variable name="i.prefix" select="substring($former, string-length($former), 1)"/>
						<xsl:variable name="i.suffix" select="substring($latter, 1, 1)"/>

						<!--
							# Identify if the opening of the prefix and the close of the suffix is a space or not.
							# Needed to confirm $shared.prefix and $shared.suffix.
						!-->
						<xsl:variable name="prefix.closed" select="not(starts-with($former, $adjacents.delimiter))"/>
						<xsl:variable name="suffix.closed" select="substring($latter, string-length($latter), 1)!=$adjacents.delimiter"/>

						<xsl:variable name="has.prefix"
							select="boolean($former/self::text()) and string-length($i.prefix) > 0 and $i.prefix != $adjacents.delimiter"/>
						<xsl:variable name="has.suffix"
							select="boolean($latter/self::text()) and string-length($i.suffix) > 0 and $i.suffix != $adjacents.delimiter"/>

						<xsl:choose>
							<xsl:when test="$has.prefix or $has.suffix">
								<xsl:variable name="split.prefix" select="str:split(normalize-space($former), $adjacents.delimiter)"/>
								<xsl:variable name="prefix" select="$split.prefix[position()=last()]/text()"/>

								<xsl:variable name="split.suffix" select="str:split(normalize-space($latter), $adjacents.delimiter)"/>
								<xsl:variable name="suffix" select="$split.suffix[position()=1]/text()"/>

								<xsl:variable name="shared.prefix"
									select="$prefix.closed and count($split.prefix) = 1 and boolean($former.element/self::*)"/>
								<xsl:variable name="shared.suffix"
									select="$suffix.closed and count($split.suffix) = 1 and boolean($latter.element/self::*)"/>

								<group type="adjacents">
									<!--
										# The evenly divided suffix/prefix in shared cases is not desired, but
										# a decision needs to be made as to where the shared field belongs
										# This method was chosen because it performs the desired split in
										# cases involving series of balanced enclosures (brackets, braces, etc).
									!-->

									<xsl:variable name="prefix.out">
										<xsl:if test="$has.prefix">
											<xsl:variable name="limit">
												<xsl:choose>
													<xsl:when test="$shared.prefix">
														<xsl:value-of select="ceiling(string-length($prefix) div 2)"/>
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of select="string-length($prefix)"/>
													</xsl:otherwise>
												</xsl:choose>
											</xsl:variable>

											<xsl:for-each select="str:split(string($prefix), '')[position() > (last()-$limit)]">
												<preceding><xsl:value-of select="text()"/></preceding>
											</xsl:for-each>
										</xsl:if>
									</xsl:variable>

									<xsl:variable name="suffix.out">
										<xsl:if test="$has.suffix">
											<xsl:variable name="limit">
												<xsl:choose>
													<xsl:when test="$shared.suffix">
														<xsl:value-of select="floor(string-length($suffix) div 2)"/>
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of select="string-length($suffix)"/>
													</xsl:otherwise>
												</xsl:choose>
											</xsl:variable>

											<xsl:for-each select="str:split(string($suffix), '')[$limit >= position()]">
												<following><xsl:value-of select="text()"/></following>
											</xsl:for-each>
										</xsl:if>
									</xsl:variable>

									<xsl:if test="$has.prefix">
										<xsl:attribute name="prefix">
											<xsl:value-of select="$prefix.out"/>
										</xsl:attribute>
									</xsl:if>

									<xsl:if test="$has.suffix">
										<xsl:attribute name="suffix">
											<xsl:value-of select="$suffix.out"/>
										</xsl:attribute>
									</xsl:if>

									<xsl:copy-of select="$prefix.out"/>
									<xsl:apply-templates select="."/>
									<xsl:copy-of select="$suffix.out"/>
								</group>
							</xsl:when>

							<xsl:otherwise>
								<!--
									# Simple copy of the paragraph element as there are no adjacent characters.
								!-->
								<xsl:copy-of select="."/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>

	<xsl:template match="@*">
		<xsl:attribute name="{name()}" namespace="{namespace-uri(.)}">
			<xsl:value-of select="."/>
		</xsl:attribute>
	</xsl:template>

	<xsl:template match="txt:*">
		<xsl:element name="{name(.)}" namespace="{namespace-uri(.)}">
			<xsl:apply-templates select="@*"/>
			<!--
				# Match everything. Only paragraph content is handled differently.
			!-->
			<xsl:apply-templates select="node()"/>
		</xsl:element>
	</xsl:template>

	<!--
		# Only used in contexts where it's not looking to group adjacent text.
	!-->
	<xsl:template match="text()">
		<xsl:value-of select="."/>
	</xsl:template>

	<xsl:template match="text()[.='']">
		<!--
			# Empty text node. Unnecessary, but kept for clarification.
		!-->
	</xsl:template>

	<xsl:template match="txt:paragraph|txt:key|txt:item[local-name(..)!='dictionary']">
		<xsl:call-template name="join"/>
	</xsl:template>

	<xsl:template match="/">
		<!--
			# Copy everything directly excepting elements that consist of paragraph content.
			# In those cases, iterate over the nodes adjusting to satisfy the grouping requirements.
		!-->
		<xsl:variable name="root" select="*"/>

		<xsl:element name="{name($root)}" namespace="{namespace-uri($root)}">
			<xsl:copy-of select="$root/@*"/>
			<xsl:copy-of select="$root/namespace::*"/>

			<xsl:apply-templates select="$root/node()|$root/processing-instruction()"/>
		</xsl:element>
	</xsl:template>
</xsl:transform>
